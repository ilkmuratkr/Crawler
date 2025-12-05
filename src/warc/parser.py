"""
WARC Parser - Extracts HTML content from WARC records
"""

import logging
import gzip
from typing import Optional, Dict
from io import BytesIO
from warcio.archiveiterator import ArchiveIterator

logger = logging.getLogger(__name__)


class WARCParser:
    """Parses WARC records and extracts HTML content"""

    @staticmethod
    def parse_warc_record(warc_data: BytesIO) -> Optional[Dict]:
        """
        Parse a WARC record and extract relevant information

        Args:
            warc_data: BytesIO containing WARC record data

        Returns:
            Dictionary with URL, headers, and HTML content, or None if parsing fails
        """
        try:
            # Try to decompress if it's gzipped
            warc_data.seek(0)
            try:
                decompressed = gzip.GzipFile(fileobj=warc_data)
                # Test if it's actually gzipped
                decompressed.read(1)
                decompressed.seek(0)
                warc_stream = decompressed
            except (gzip.BadGzipFile, OSError):
                # Not gzipped, use as is
                warc_data.seek(0)
                warc_stream = warc_data

            # Parse WARC using warcio
            for record in ArchiveIterator(warc_stream):
                # We're interested in response records
                if record.rec_type != 'response':
                    continue

                # Extract URL
                url = record.rec_headers.get_header('WARC-Target-URI')

                # Extract HTTP headers
                http_headers = {}
                if hasattr(record, 'http_headers') and record.http_headers:
                    http_headers = {
                        k: v for k, v in record.http_headers.headers
                    }

                # Extract content
                content = record.content_stream().read()

                # Decode content if it's bytes
                if isinstance(content, bytes):
                    # Try to detect encoding from headers
                    content_type = http_headers.get('Content-Type', '')
                    encoding = 'utf-8'  # Default

                    if 'charset=' in content_type.lower():
                        try:
                            encoding = content_type.lower().split('charset=')[1].split(';')[0].strip()
                        except:
                            pass

                    try:
                        content = content.decode(encoding, errors='ignore')
                    except:
                        # If decoding fails, try utf-8 with ignore
                        content = content.decode('utf-8', errors='ignore')

                return {
                    'url': url,
                    'headers': http_headers,
                    'content': content,
                    'status': record.http_headers.get_statuscode() if hasattr(record, 'http_headers') else None,
                }

        except Exception as e:
            logger.error(f"Failed to parse WARC record: {e}")
            return None

        return None

    @staticmethod
    def extract_html(warc_data: BytesIO) -> Optional[str]:
        """
        Extract just the HTML content from a WARC record

        Args:
            warc_data: BytesIO containing WARC record

        Returns:
            HTML content as string, or None if not found
        """
        parsed = WARCParser.parse_warc_record(warc_data)
        if parsed and parsed.get('content'):
            content_type = parsed.get('headers', {}).get('Content-Type', '')
            # Only return if it's HTML
            if 'html' in content_type.lower():
                return parsed['content']
        return None

    @staticmethod
    def is_html_response(warc_data: BytesIO) -> bool:
        """
        Check if WARC record contains an HTML response

        Args:
            warc_data: BytesIO containing WARC record

        Returns:
            True if record contains HTML
        """
        parsed = WARCParser.parse_warc_record(warc_data)
        if not parsed:
            return False

        content_type = parsed.get('headers', {}).get('Content-Type', '')
        return 'html' in content_type.lower()

    @staticmethod
    def extract_metadata(warc_data: BytesIO) -> Optional[Dict]:
        """
        Extract metadata from WARC record without full content

        Args:
            warc_data: BytesIO containing WARC record

        Returns:
            Dictionary with URL, status, headers (without full content)
        """
        parsed = WARCParser.parse_warc_record(warc_data)
        if not parsed:
            return None

        # Return metadata without large content
        return {
            'url': parsed.get('url'),
            'status': parsed.get('status'),
            'content_type': parsed.get('headers', {}).get('Content-Type'),
            'content_length': len(parsed.get('content', '')),
        }
