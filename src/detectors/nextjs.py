"""
Next.js Detection Module
Detects Next.js usage through multiple indicators
"""

import re
import logging
import warnings
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suppress BeautifulSoup XML warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logger = logging.getLogger(__name__)


class NextJsDetector:
    """Detects Next.js usage in HTML content"""

    # Next.js indicators with different confidence levels
    HIGH_CONFIDENCE_PATTERNS = [
        r'__NEXT_DATA__',  # Next.js data script tag (en yaygın!)
        r'"__NEXT_LOADED_PAGES__"',  # Next.js loaded pages
        r'self\.__next',  # Next.js self reference
        r'window\.__NEXT_DATA__',  # Window Next.js data
        r'<div id="__next"',  # Next.js root div
        r'id="__NEXT_DATA__"',  # Script tag id
        r'"buildId"',  # Build ID in Next.js data
    ]

    MEDIUM_CONFIDENCE_PATTERNS = [
        r'/_next/static/',  # Next.js static assets
        r'/_next/data/',  # Next.js data fetching
        r'/_next/image',  # Next.js image optimization
        r'next-route-announcer',  # Next.js accessibility feature
        r'__next-error-boundary',  # Next.js error boundary
        r'data-nextjs-scroll-focus-boundary',  # Next.js scroll feature
        r'/_next/webpack',  # Webpack chunks
        r'__BUILD_MANIFEST',  # Build manifest
        r'__NEXT_P',  # Next.js page indicator
    ]

    LOW_CONFIDENCE_PATTERNS = [
        r'/_next/',  # Generic Next.js path (could be false positive)
        r'next\.js',  # Mention of next.js (could be in comments)
        r'nextjs',  # Mention of nextjs
    ]

    BUILD_ID_PATTERN = r'/_next/static/([a-zA-Z0-9_-]+)/'
    VERSION_PATTERN = r'Next\.js\s+v?(\d+\.\d+\.\d+)'

    def __init__(self):
        self.high_regex = [re.compile(p, re.IGNORECASE) for p in self.HIGH_CONFIDENCE_PATTERNS]
        self.medium_regex = [re.compile(p, re.IGNORECASE) for p in self.MEDIUM_CONFIDENCE_PATTERNS]
        self.low_regex = [re.compile(p, re.IGNORECASE) for p in self.LOW_CONFIDENCE_PATTERNS]
        self.build_id_regex = re.compile(self.BUILD_ID_PATTERN)
        self.version_regex = re.compile(self.VERSION_PATTERN)

    def detect(self, html: str, url: str = "") -> Dict:
        """
        Detect Next.js usage in HTML content

        Args:
            html: HTML content as string
            url: URL of the page (optional, for logging)

        Returns:
            Dictionary with detection results:
            {
                'is_nextjs': bool,
                'confidence': 'high' | 'medium' | 'low',
                'indicators': List[str],
                'build_id': Optional[str],
                'version': Optional[str],
                'meta_tags': Dict
            }
        """
        if not html:
            return self._no_detection()

        indicators = []
        confidence_scores = []

        # Check high confidence patterns
        for pattern in self.high_regex:
            if pattern.search(html):
                indicators.append(pattern.pattern)
                confidence_scores.append(3)  # High confidence

        # Check medium confidence patterns
        for pattern in self.medium_regex:
            if pattern.search(html):
                indicators.append(pattern.pattern)
                confidence_scores.append(2)  # Medium confidence

        # Check low confidence patterns
        for pattern in self.low_regex:
            if pattern.search(html):
                indicators.append(pattern.pattern)
                confidence_scores.append(1)  # Low confidence

        # Extract build ID
        build_id = self._extract_build_id(html)
        if build_id:
            indicators.append(f'build_id:{build_id}')
            confidence_scores.append(3)

        # Extract version
        version = self._extract_version(html)

        # Parse meta tags and check for Next.js specific ones
        meta_tags = self._extract_meta_tags(html)
        if meta_tags:
            indicators.append('nextjs_meta_tags')
            confidence_scores.append(2)

        # Determine if it's Next.js
        is_nextjs = len(indicators) > 0

        # Calculate confidence level
        if not is_nextjs:
            confidence = None
        else:
            max_score = max(confidence_scores) if confidence_scores else 0
            if max_score >= 3 or sum(confidence_scores) >= 5:
                confidence = 'high'
            elif max_score >= 2 or sum(confidence_scores) >= 3:
                confidence = 'medium'
            else:
                confidence = 'low'

        result = {
            'is_nextjs': is_nextjs,
            'confidence': confidence,
            'indicators': list(set(indicators)),  # Remove duplicates
            'build_id': build_id,
            'version': version,
            'meta_tags': meta_tags,
            'url': url
        }

        if is_nextjs:
            logger.info(
                f"Next.js detected on {url} "
                f"(confidence: {confidence}, indicators: {len(indicators)})"
            )

        return result

    def _extract_build_id(self, html: str) -> Optional[str]:
        """Extract Next.js build ID"""
        match = self.build_id_regex.search(html)
        return match.group(1) if match else None

    def _extract_version(self, html: str) -> Optional[str]:
        """Extract Next.js version if mentioned"""
        match = self.version_regex.search(html)
        return match.group(1) if match else None

    def _extract_meta_tags(self, html: str) -> Dict[str, str]:
        """Extract Next.js related meta tags"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            meta_tags = {}

            # Look for common Next.js meta tags
            nextjs_meta_patterns = [
                'next-head-count',
                'next-font',
                '__next',
            ]

            for meta in soup.find_all('meta'):
                name = meta.get('name', '') or meta.get('property', '')
                content = meta.get('content', '')

                for pattern in nextjs_meta_patterns:
                    if pattern.lower() in name.lower():
                        meta_tags[name] = content

            # Check for Next.js specific tags
            if soup.find('div', id='__next'):
                meta_tags['__next_root'] = 'found'

            if soup.find('script', id='__NEXT_DATA__'):
                meta_tags['__NEXT_DATA__'] = 'found'

            return meta_tags

        except Exception as e:
            logger.warning(f"Failed to parse meta tags: {e}")
            return {}

    def _no_detection(self) -> Dict:
        """Return negative detection result"""
        return {
            'is_nextjs': False,
            'confidence': None,
            'indicators': [],
            'build_id': None,
            'version': None,
            'meta_tags': {},
            'url': ''
        }

    def detect_batch(self, html_list: List[tuple]) -> List[Dict]:
        """
        Detect Next.js in multiple HTML documents

        Args:
            html_list: List of tuples (url, html)

        Returns:
            List of detection results
        """
        results = []
        for url, html in html_list:
            result = self.detect(html, url)
            if result['is_nextjs']:
                results.append(result)
        return results

    def filter_high_confidence(self, results: List[Dict]) -> List[Dict]:
        """Filter results to only high confidence detections"""
        return [r for r in results if r['confidence'] == 'high']

    def filter_by_confidence(self, results: List[Dict], min_confidence: str = 'medium') -> List[Dict]:
        """
        Filter results by minimum confidence level

        Args:
            results: List of detection results
            min_confidence: 'high', 'medium', or 'low'

        Returns:
            Filtered results
        """
        confidence_order = {'low': 1, 'medium': 2, 'high': 3}
        min_level = confidence_order.get(min_confidence, 2)

        return [
            r for r in results
            if r['confidence'] and confidence_order.get(r['confidence'], 0) >= min_level
        ]
