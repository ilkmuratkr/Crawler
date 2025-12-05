"""
Advanced Retry Handler with Failure Tracking
5 deneme, her başarısızlıkta 5 dakika bekleme, başarısız olanları kaydetme
"""

import time
import json
import logging
from typing import Callable, Any, Optional, Dict, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FailureReason(Enum):
    """Başarısızlık sebepleri"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"


@dataclass
class FailedTask:
    """Başarısız görev kaydı"""
    url: str
    warc_path: str
    failure_reason: str
    failure_count: int
    last_attempt: str
    error_message: str
    first_failed: str


class FailureTracker:
    """Başarısız görevleri takip eder ve kaydeder"""

    def __init__(self, output_dir: str = "data/failures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.failed_tasks: Dict[str, FailedTask] = {}
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def add_failure(
        self,
        warc_path: str,
        reason: FailureReason,
        error: Exception,
        attempt: int
    ):
        """
        Başarısızlık kaydet

        Args:
            warc_path: WARC dosya yolu
            reason: Başarısızlık sebebi
            error: Exception objesi
            attempt: Kaçıncı deneme
        """
        now = datetime.now().isoformat()

        if warc_path in self.failed_tasks:
            # Mevcut kayıt güncelle
            task = self.failed_tasks[warc_path]
            task.failure_count = attempt
            task.last_attempt = now
            task.error_message = str(error)
        else:
            # Yeni kayıt oluştur
            self.failed_tasks[warc_path] = FailedTask(
                url=f"https://data.commoncrawl.org/{warc_path}",
                warc_path=warc_path,
                failure_reason=reason.value,
                failure_count=attempt,
                last_attempt=now,
                error_message=str(error),
                first_failed=now
            )

        logger.warning(
            f"Failure recorded: {warc_path} "
            f"(attempt {attempt}/5, reason: {reason.value})"
        )

    def save_failures(self) -> str:
        """
        Başarısızlıkları dosyaya kaydet

        Returns:
            Kaydedilen dosyanın yolu
        """
        if not self.failed_tasks:
            logger.info("No failures to save")
            return ""

        filename = f"failed_warcs_{self.session_id}.json"
        filepath = self.output_dir / filename

        # JSON formatında kaydet
        failures_list = [asdict(task) for task in self.failed_tasks.values()]

        with open(filepath, 'w') as f:
            json.dump({
                'session_id': self.session_id,
                'total_failures': len(failures_list),
                'generated_at': datetime.now().isoformat(),
                'failures': failures_list
            }, f, indent=2)

        logger.info(f"Saved {len(failures_list)} failures to {filepath}")

        # Ayrıca basit text dosyası oluştur (kolay retry için)
        txt_filepath = self.output_dir / f"failed_warcs_{self.session_id}.txt"
        with open(txt_filepath, 'w') as f:
            for task in self.failed_tasks.values():
                f.write(f"{task.warc_path}\n")

        logger.info(f"Saved failure paths to {txt_filepath}")

        return str(filepath)

    def load_failures(self, filepath: str) -> List[str]:
        """
        Önceki başarısızlıkları yükle

        Args:
            filepath: JSON veya TXT dosya yolu

        Returns:
            WARC path'lerinin listesi
        """
        filepath = Path(filepath)

        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return []

        if filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
                failures = data.get('failures', [])
                return [f['warc_path'] for f in failures]

        elif filepath.suffix == '.txt':
            with open(filepath, 'r') as f:
                return [line.strip() for line in f if line.strip()]

        else:
            logger.error(f"Unsupported file format: {filepath}")
            return []

    def get_statistics(self) -> Dict:
        """Başarısızlık istatistikleri"""
        if not self.failed_tasks:
            return {
                'total': 0,
                'by_reason': {}
            }

        by_reason = {}
        for task in self.failed_tasks.values():
            reason = task.failure_reason
            by_reason[reason] = by_reason.get(reason, 0) + 1

        return {
            'total': len(self.failed_tasks),
            'by_reason': by_reason,
            'session_id': self.session_id
        }


class RetryHandler:
    """
    Gelişmiş retry handler
    - 5 deneme
    - Her başarısızlıkta 5 dakika bekleme
    - Başarısızlıkları kaydetme
    - Proxy rotation (her retry'da farklı proxy)
    """

    def __init__(
        self,
        max_retries: int = 5,
        retry_delay: int = 300,  # 5 dakika = 300 saniye
        failure_tracker: Optional[FailureTracker] = None,
        proxy_manager: Optional[Any] = None
    ):
        """
        Initialize retry handler

        Args:
            max_retries: Maksimum deneme sayısı
            retry_delay: Her deneme arası bekleme süresi (saniye)
            failure_tracker: Başarısızlık tracker (opsiyonel)
            proxy_manager: ProxyManager instance (opsiyonel)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.failure_tracker = failure_tracker or FailureTracker()
        self.proxy_manager = proxy_manager

    def execute_with_retry(
        self,
        func: Callable,
        warc_path: str,
        current_proxy=None,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Fonksiyonu retry logic ile çalıştır

        Args:
            func: Çalıştırılacak fonksiyon
            warc_path: WARC dosya yolu (tracking için)
            current_proxy: Şu anki kullanılan proxy (rotation için)
            *args, **kwargs: Fonksiyon parametreleri

        Returns:
            Fonksiyon sonucu veya None (başarısızlık durumunda)
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Proxy rotation (retry'larda farklı proxy kullan)
                if attempt > 1 and self.proxy_manager and current_proxy:
                    new_proxy = self.proxy_manager.get_next_proxy(current_proxy)
                    logger.info(
                        f"Switching proxy for retry {attempt}: "
                        f"{current_proxy.vpn_ip} -> {new_proxy.vpn_ip}"
                    )
                    current_proxy = new_proxy
                    # Update kwargs with new proxy
                    kwargs['current_proxy'] = current_proxy

                logger.debug(f"Attempt {attempt}/{self.max_retries}: {warc_path}")

                # Fonksiyonu çalıştır
                result = func(*args, **kwargs)

                # Başarılı!
                if attempt > 1:
                    logger.info(f"Success on attempt {attempt}: {warc_path}")

                return result

            except TimeoutError as e:
                last_error = e
                reason = FailureReason.TIMEOUT
                logger.warning(f"Timeout on attempt {attempt}: {warc_path}")

            except ConnectionError as e:
                last_error = e
                reason = FailureReason.CONNECTION_ERROR
                logger.warning(f"Connection error on attempt {attempt}: {warc_path}")

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                if 'timeout' in error_str:
                    reason = FailureReason.TIMEOUT
                elif 'connection' in error_str or 'network' in error_str:
                    reason = FailureReason.CONNECTION_ERROR
                elif 'http' in error_str or 'status' in error_str:
                    reason = FailureReason.HTTP_ERROR
                elif 'parse' in error_str:
                    reason = FailureReason.PARSE_ERROR
                else:
                    reason = FailureReason.UNKNOWN

                logger.warning(
                    f"Error on attempt {attempt}/{self.max_retries}: {warc_path} - {e}"
                )

            # Son denemeyse başarısızlığı kaydet
            if attempt == self.max_retries:
                self.failure_tracker.add_failure(
                    warc_path=warc_path,
                    reason=reason,
                    error=last_error,
                    attempt=attempt
                )
                logger.error(
                    f"Failed after {self.max_retries} attempts: {warc_path}"
                )
                return None

            # Bekleme süresi (son denemeden sonra bekleme yok)
            if attempt < self.max_retries:
                logger.info(f"Waiting {self.retry_delay}s before retry...")
                time.sleep(self.retry_delay)

        return None

    def save_failures(self) -> str:
        """Başarısızlıkları kaydet"""
        return self.failure_tracker.save_failures()

    def get_statistics(self) -> Dict:
        """İstatistikleri al"""
        return self.failure_tracker.get_statistics()


class QuickRetryHandler(RetryHandler):
    """
    Hızlı retry handler (test için)
    Daha kısa bekleme süreleri
    """

    def __init__(self, failure_tracker: Optional[FailureTracker] = None):
        super().__init__(
            max_retries=3,
            retry_delay=10,  # 10 saniye
            failure_tracker=failure_tracker
        )
