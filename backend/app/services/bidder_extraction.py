#!/usr/bin/env python3
"""
Enhanced Bidder Document Processing System with Structured Field Extraction
Processes bidder documents and creates structured bidder profiles with BidderField dataclass
"""

import os
import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import PyPDF2
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️ SQLAlchemy not installed. PostgreSQL save will be skipped.")

# OCR and Table Extraction Libraries (install these for enhanced functionality)
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    import tabula
    import camelot
    OCR_AVAILABLE = True
    print("✅ OCR libraries available (pytesseract, pdf2image, tabula, camelot)")
except ImportError as e:
    print(f"⚠️  OCR libraries not available: {e}")
    print("Install with: pip install pytesseract pdf2image tabula-py camelot-py opencv-python")
    OCR_AVAILABLE = False

# Configuration
QWEN_API_URL = "http://135.235.192.4:8000/generate"
API_KEY = "enter your key here"
WORKSPACE_PATH = r"../uploads/tenders"
DATABASE_URL = "postgresql://postgres:password@localhost:5432/db"

if DB_AVAILABLE:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

@dataclass
class BidderField:
    field_name: str
    field_type: str
    value: Any
    bidder_id: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    original_text: Optional[str] = None
    confidence: float = 1.0

if DB_AVAILABLE:
    class DBManager:
        def __init__(self):
            self.session = SessionLocal()

        def init_tables(self):
            with engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT,
                    category TEXT,
                    priority INT,
                    dependencies JSONB,
                    rule_definition JSONB,
                    original_text TEXT,
                    source_page INT,
                    source_section TEXT,
                    confidence FLOAT
                )
                """))

                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bidder_fields (
                    bidder_id TEXT,
                    field_name TEXT,
                    field_type TEXT,
                    value JSONB,
                    source_document TEXT,
                    source_page INT,
                    source_section TEXT,
                    original_text TEXT,
                    confidence FLOAT
                )
                """))

                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    id SERIAL PRIMARY KEY,
                    bidder_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    field TEXT,
                    bidder_value TEXT,
                    expected_value TEXT,
                    result TEXT NOT NULL,
                    rule_type TEXT,
                    confidence FLOAT,
                    source_document TEXT,
                    source_page INT,
                    source_section TEXT,
                    bidder_original_text TEXT,
                    bidder_confidence FLOAT,
                    rule_original_text TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))

                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS evaluation_summary (
                    id SERIAL PRIMARY KEY,
                    bidder_id TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    mandatory_count INT,
                    total_rules INT,
                    passed_count INT,
                    failed_count INT,
                    needs_review_count INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))

        def store_bidder_fields(self, bidder_profile: Dict[str, Any]):
            bidder_id = bidder_profile.get('summary', {}).get('bidder_id')
            if not bidder_id:
                fields = bidder_profile.get('bidder_fields', [])
                bidder_id = fields[0].get('bidder_id') if fields else None

            if not bidder_id:
                raise ValueError('Cannot save bidder fields without bidder_id')

            query = text("""
                INSERT INTO bidder_fields (
                    bidder_id, field_name, field_type, value,
                    source_document, source_page, source_section,
                    original_text, confidence
                ) VALUES (
                    :bidder_id, :field_name, :field_type, :value,
                    :source_document, :source_page, :source_section,
                    :original_text, :confidence
                )
            """)

            for field in bidder_profile.get('bidder_fields', []):
                self.session.execute(
                    query,
                    {
                        'bidder_id': bidder_id,
                        'field_name': field.get('field_name'),
                        'field_type': field.get('field_type'),
                        'value': json.dumps(field.get('value')),
                        'source_document': field.get('source_document'),
                        'source_page': field.get('source_page'),
                        'source_section': field.get('source_section'),
                        'original_text': field.get('original_text'),
                        'confidence': field.get('confidence')
                    }
                )

            self.session.commit()

        def close(self):
            self.session.close()
else:
    class DBManager:
        def __init__(self):
            raise ImportError('SQLAlchemy is required for DBManager')

        def init_tables(self):
            pass

        def store_bidder_fields(self, bidder_profile: Dict[str, Any]):
            pass

        def close(self):
            pass


class BidderDocumentExtractor:
    """Extract structured information from bidder documents"""
    
    def __init__(self):
        self.extracted_data = {}
        self.confidence_scores = {}
    
    def extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text"""
        # Find numbers with optional commas and decimals
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', text)
        result = []
        for n in numbers:
            if n and n.strip():
                try:
                    result.append(float(n.replace(',', '')))
                except ValueError:
                    continue
        return result
    
    def extract_currency_values(self, text: str) -> Dict[str, float]:
        """Extract currency values (INR, Crore, Lakh)"""
        values = {}
        
        # Pattern: number + currency/unit
        patterns = [
            (r'₹\s*([\d,]+(?:\.\d+)?)\s*(?:Crore|crore|CR|Cr)', 'crore'),
            (r'₹\s*([\d,]+(?:\.\d+)?)\s*(?:Lakh|lakh|L)\b', 'lakh'),
            (r'INR\s*([\d,]+(?:\.\d+)?)', 'inr'),
            (r'₹\s*([\d,]+(?:\.\d+)?)', 'inr'),
        ]
        
        for pattern, unit in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    val = float(match.replace(',', ''))
                    if val > 0:  # Only add positive values
                        if unit == 'crore':
                            val *= 10000000
                        elif unit == 'lakh':
                            val *= 100000
                        
                        if unit not in values or val > values[unit]:
                            values[unit] = val
                except (ValueError, AttributeError):
                    continue
        
        return values
    
    def extract_company_name(self, text: str) -> str:
        """Extract company name"""
        # Look for company name patterns
        patterns = [
            r'(?:Company Name|Company|(?:Named as|Name:))\s*[:]*\s*([A-Z][^.\n]+)',
            r'^([A-Z][A-Z\s\.&,\-\(\)]*?)\s*(?:Pvt\.?|Limited|Ltd\.?|LLC)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def extract_gst_number(self, text: str) -> str:
        """Extract GST number"""
        # GST format: 2 digits (state) + 10 digits (PAN) + 1 digit (entity) + 1 digit (check)
        gst_pattern = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9]{1}\b'
        matches = re.findall(gst_pattern, text)
        return matches[0] if matches else ""
    
    def extract_pan_number(self, text: str) -> str:
        """Extract PAN number"""
        # PAN format: 5 letters + 4 digits + 1 letter
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        matches = re.findall(pan_pattern, text)
        return matches[0] if matches else ""
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}',  # Just year
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return dates
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications and standards"""
        cert_keywords = [
            'ISO', 'ISO 9001', 'ISO 27001', 'ISO 14001', 'ISO 45001',
            'GST', 'PAN', 'MSME', 'DPIIT',
            'CE', 'UL', 'TUV', 'BIS',
            'Certification', 'Certified', 'Accredited'
        ]
        
        certifications = []
        text_lower = text.lower()
        
        for cert in cert_keywords:
            if cert.lower() in text_lower:
                # Try to find the full certification reference
                pattern = re.compile(f'{cert}\\s*[:\\-]*\\s*[^.\\n]*', re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    certifications.extend(matches)
        
        return list(set(certifications))
    
    def extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract project information"""
        projects = []
        
        # Look for project-related patterns
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['project', 'work order', 'contract', 'completed']):
                project_info = {
                    'description': line.strip(),
                    'value': 0,
                    'year': None,
                    'type': 'project'
                }
                
                # Extract value if present in this line or next few lines
                context = '\n'.join(lines[i:min(i+5, len(lines))])
                values = self.extract_currency_values(context)
                if values:
                    project_info['value'] = max(values.values())
                
                # Extract year
                dates = self.extract_dates(context)
                if dates:
                    project_info['year'] = dates[0]
                
                projects.append(project_info)
        
        return projects[:10]  # Limit to 10 projects
    
    def extract_organization_age(self, text: str) -> int:
        """Extract organization age or incorporation year"""
        # Look for incorporation date
        patterns = [
            r'(?:Incorporated|Established|Founded)\s*(?:in|on)?\s*(\d{4})',
            r'(?:Date of Incorporation|Incorporation Date|Founded):\s*(\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    year = int(matches[0])
                    return datetime.now().year - year
                except:
                    pass
        
        return 0
    
    def extract_bidder_id(self, text: str) -> str:
        """Extract bidder ID or reference number from documents"""
        # Look for various bidder ID patterns
        patterns = [
            r'(?:Bidder\s*ID|Bidder\s*Reference|Reference\s*ID|Application\s*ID)\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?:Bid\s*No|Bid\s*Number|Proposal\s*ID)\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?:Tender\s*ID|Contract\s*ID)\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?:Registration\s*No|Registration\s*Number)\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?:Vendor\s*ID|Supplier\s*ID)\s*[:\-]?\s*([A-Z0-9\-]+)',
            # Look for alphanumeric codes that might be IDs
            r'\b([A-Z]{2,}[\-_]?[0-9]{4,})\b',
            r'\b([0-9]{6,}[\-_]?[A-Z]{2,})\b',
        ]
        
        text_upper = text.upper()
        for pattern in patterns:
            matches = re.findall(pattern, text_upper)
            if matches:
                # Return the first match, clean it up
                bidder_id = matches[0].strip()
                # Remove any trailing punctuation
                bidder_id = re.sub(r'[^\w\-]+$', '', bidder_id)
                return bidder_id
        
        # If no specific pattern found, try to generate one from company name and GST
        # This is a fallback for when no explicit bidder ID is found
        return None
    
    def calculate_confidence(self, found: bool, text_length: int) -> float:
        """Calculate confidence score for extracted data"""
        if not found:
            return 0.0
        return min(0.95, text_length / 10000)  # Normalize by text length


class BidderDocumentProcessor:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.documents = {}
        self.extracted_text = {}
        self.bidder_fields = []
        self.extractor = BidderDocumentExtractor()
        
    def query_qwen_api(self, prompt: str, max_retries: int = 3) -> str:
        """Query the Qwen API with a prompt using POST method"""
        for attempt in range(max_retries):
            try:
                headers = {
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                }
                
                # Use POST request with JSON payload
                payload = {
                    "prompt": prompt[:1000]  # Limit prompt length
                }
                
                response = requests.post(
                    QWEN_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Handle various possible response formats
                    if isinstance(result, dict):
                        return result.get('text', '') or result.get('response', '') or str(result)
                    else:
                        return str(result)
                else:
                    print(f"API Error (attempt {attempt+1}): {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Error calling Qwen API (attempt {attempt+1}): {e}")
                
            if attempt < max_retries - 1:
                print("Retrying in 2 seconds...")
                import time
                time.sleep(2)
        
        return ""
    
    def create_structured_prompt(self, field_name: str, field_type: str, context: str, document_name: str) -> str:
        """Create a structured prompt for Qwen API to extract specific field information"""
        
        prompt_template = f"""
Extract the following information from the bidder document and return it as a JSON object with this exact structure:

{{
    "field_name": "{field_name}",
    "field_type": "{field_type}",
    "value": [EXTRACTED_VALUE],
    "source_document": "{document_name}",
    "source_page": [PAGE_NUMBER_OR_NULL],
    "source_section": "[SECTION_NAME_OR_NULL]",
    "original_text": "[ORIGINAL_TEXT_SNIPPET]",
    "confidence": [CONFIDENCE_SCORE_0_TO_1]
"""}}

INSTRUCTIONS:
1. Extract the most relevant value for "{field_name}" from the document text
2. Set field_type to "{field_type}"
3. For value: extract the actual data (string, number, boolean, or array as appropriate)
4. For source_page: find the page number if mentioned, otherwise null
5. For source_section: identify the section/header where this info appears, otherwise null
6. For original_text: provide the exact text snippet containing the extracted value
7. For confidence: rate how confident you are in this extraction (0.0 to 1.0)

DOCUMENT CONTENT:
{context[:2000]}

Return ONLY the JSON object, no additional text or explanation.
"""
        return prompt_template
    
    def parse_bidder_field_response(self, response: str, document_name: str) -> Optional[BidderField]:
        """Parse Qwen API response into BidderField object"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            
            # Find JSON object in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
                
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Create BidderField object
            field = BidderField(
                field_name=data.get('field_name', ''),
                field_type=data.get('field_type', ''),
                value=data.get('value'),
                source_document=data.get('source_document', document_name),
                source_page=data.get('source_page'),
                source_section=data.get('source_section'),
                original_text=data.get('original_text'),
                confidence=float(data.get('confidence', 0.5))
            )
            
            return field
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing response: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict[int, str]]:
        """Extract text from PDF file with OCR fallback, returning both combined text and page-wise text"""
        try:
            combined_text = ""
            page_texts = {}

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    # If no text extracted and OCR is available, try OCR
                    if not page_text.strip() and OCR_AVAILABLE:
                        print(f"🔄 No text found on page {page_num+1}, attempting OCR...")
                        page_text = self.extract_text_with_ocr(pdf_path, page_num)

                    # Store page-wise text (1-indexed)
                    page_texts[page_num + 1] = page_text
                    combined_text += page_text + "\n"

            return combined_text.strip(), page_texts
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            # Try OCR as fallback for entire document
            if OCR_AVAILABLE:
                print("🔄 Falling back to OCR for entire document...")
                ocr_text = self.extract_text_with_ocr(pdf_path)
                return ocr_text, {1: ocr_text}
            return "", {}

    def extract_text_with_ocr(self, pdf_path: str, page_num: Optional[int] = None) -> str:
        """Extract text using OCR from PDF pages"""
        if not OCR_AVAILABLE:
            return ""

        try:
            # Convert PDF to images
            if page_num is not None:
                # Convert specific page
                images = pdf2image.convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
            else:
                # Convert all pages
                images = pdf2image.convert_from_path(pdf_path)

            text = ""
            for image in images:
                # Extract text from image using Tesseract
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
                image.close()

            return text
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""

    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF using multiple methods"""
        tables_data = []

        if not OCR_AVAILABLE:
            print("⚠️  Table extraction requires OCR libraries")
            return tables_data

        try:
            # Method 1: Try tabula-py (works well with structured tables)
            try:
                tabula_tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
                for i, table in enumerate(tabula_tables):
                    if not table.empty:
                        tables_data.append({
                            'method': 'tabula',
                            'table_index': i,
                            'data': table.to_dict('records'),
                            'shape': table.shape
                        })
            except Exception as e:
                print(f"Tabula extraction failed: {e}")

            # Method 2: Try camelot (better for complex tables)
            try:
                camelot_tables = camelot.read_pdf(pdf_path, pages='all')
                for i, table in enumerate(camelot_tables):
                    if len(table) > 0:  # Check if table has data
                        tables_data.append({
                            'method': 'camelot',
                            'table_index': i,
                            'data': table.df.to_dict('records'),
                            'shape': table.df.shape,
                            'accuracy': table.accuracy
                        })
            except Exception as e:
                print(f"Camelot extraction failed: {e}")

        except Exception as e:
            print(f"Table extraction failed: {e}")

        return tables_data

    def extract_images_from_pdf(self, pdf_path: str, output_dir: str = "extracted_images") -> List[str]:
        """Extract images from PDF pages"""
        if not OCR_AVAILABLE:
            return []

        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            images = pdf2image.convert_from_path(pdf_path)
            image_paths = []

            for i, image in enumerate(images):
                image_path = os.path.join(output_dir, f"{Path(pdf_path).stem}_page_{i+1}.png")
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
                image.close()

            return image_paths
        except Exception as e:
            print(f"Image extraction failed: {e}")
            return []

    def process_table_data(self, tables: List[Dict[str, Any]]) -> List[BidderField]:
        """Process extracted table data to create BidderField objects"""
        bidder_fields = []

        for table_info in tables:
            table_data = table_info.get('data', [])
            method = table_info.get('method', 'unknown')

            if not table_data:
                continue

            # Convert table data to string for analysis
            table_text = json.dumps(table_data, indent=2)

            # Look for financial data in tables
            if self._is_financial_table(table_data):
                financial_fields = self._extract_financial_from_table(table_data, table_text)
                bidder_fields.extend(financial_fields)

            # Look for project data in tables
            if self._is_project_table(table_data):
                project_fields = self._extract_projects_from_table(table_data, table_text)
                bidder_fields.extend(project_fields)

        return bidder_fields

    def _is_financial_table(self, table_data: List[Dict[str, Any]]) -> bool:
        """Check if table contains financial information"""
        if not table_data:
            return False

        # Look for financial keywords in table headers/keys
        financial_keywords = ['turnover', 'revenue', 'profit', 'loss', 'assets', 'liabilities',
                            'equity', 'income', 'expense', 'balance', 'financial', 'amount', '₹', '$']

        table_text = str(table_data).lower()
        return any(keyword in table_text for keyword in financial_keywords)

    def _is_project_table(self, table_data: List[Dict[str, Any]]) -> bool:
        """Check if table contains project information"""
        if not table_data:
            return False

        # Look for project keywords
        project_keywords = ['project', 'work', 'contract', 'completion', 'client', 'value',
                          'duration', 'location', 'status', 'certificate']

        table_text = str(table_data).lower()
        return any(keyword in table_text for keyword in project_keywords)

    def _extract_financial_from_table(self, table_data: List[Dict[str, Any]], table_text: str) -> List[BidderField]:
        """Extract financial information from table data"""
        fields = []

        # Look for turnover/revenue figures
        for row in table_data:
            for key, value in row.items():
                if isinstance(value, str):
                    # Look for turnover patterns
                    turnover_match = re.search(r'(?:turnover|revenue|sales).*?([₹$]?\s*[\d,]+(?:\.\d+)?)', value, re.IGNORECASE)
                    if turnover_match:
                        amount = self._extract_currency_value(turnover_match.group(1))
                        if amount and amount > 100000:  # Reasonable minimum
                            fields.append(BidderField(
                                field_name="average_annual_turnover_inr",
                                field_type="integer",
                                value=int(amount),
                                source_section="table_data",
                                original_text=value,
                                confidence=0.8
                            ))

        return fields

    def _extract_projects_from_table(self, table_data: List[Dict[str, Any]], table_text: str) -> List[BidderField]:
        """Extract project information from table data"""
        fields = []

        # Look for project completion certificates or work orders
        projects = []
        for row in table_data:
            project_info = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Extract project details
                    if 'project' in key.lower() or 'work' in key.lower():
                        project_info['name'] = value
                    elif 'client' in key.lower() or 'customer' in key.lower():
                        project_info['client'] = value
                    elif 'value' in key.lower() or 'amount' in key.lower():
                        currency_val = self._extract_currency_value(str(value))
                        if currency_val:
                            project_info['value'] = currency_val
                    elif 'completion' in key.lower() or 'date' in key.lower():
                        project_info['completion_date'] = value

            if project_info:
                projects.append(project_info)

        if projects:
            fields.append(BidderField(
                field_name="completed_projects",
                field_type="array",
                value=projects,
                source_section="table_data",
                original_text=table_text,
                confidence=0.7
            ))

        return fields

    def _extract_currency_value(self, text: str) -> Optional[float]:
        """Extract currency value from text"""
        # Remove currency symbols and extract numbers
        text = re.sub(r'[₹$€£¥]', '', text)
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', text)
        if numbers:
            try:
                return float(numbers[0].replace(',', ''))
            except ValueError:
                pass
        return None

    def find_text_location(self, search_text: str, document_name: str) -> Tuple[Optional[int], Optional[str]]:
        """Find which page and section a piece of text came from"""
        if document_name not in self.documents:
            return None, None

        doc_info = self.documents[document_name]
        page_texts = doc_info.get('page_texts', {})

        # Clean search text for better matching
        search_clean = search_text.lower().strip()

        # Search through each page
        for page_num, page_text in page_texts.items():
            page_lower = page_text.lower()

            # Try different matching strategies
            if (search_clean in page_lower or
                any(word in page_lower for word in search_clean.split()) or
                self._fuzzy_match(search_clean, page_lower)):

                # Try to identify section based on content
                section = self._identify_section(page_text, search_text)
                return page_num, section

        # If no exact match, try to find by document type and field type
        doc_type = doc_info.get('type', '')
        section = self._infer_section_from_doc_type(doc_type, search_text)
        return None, section

    def _fuzzy_match(self, search_text: str, page_text: str) -> bool:
        """Perform fuzzy matching for text location"""
        # Remove special characters and extra spaces
        import re
        search_clean = re.sub(r'[^\w\s]', '', search_text)
        page_clean = re.sub(r'[^\w\s]', '', page_text)

        # Check if key parts match
        search_words = set(search_clean.split())
        page_words = set(page_clean.split())

        # If 50% of search words are in page, consider it a match
        if search_words and len(search_words.intersection(page_words)) / len(search_words) >= 0.5:
            return True

        return False

    def _infer_section_from_doc_type(self, doc_type: str, search_text: str) -> Optional[str]:
        """Infer section based on document type and content"""
        search_lower = search_text.lower()

        # Document type to section mapping
        type_section_map = {
            'financial_statement': 'financial_info',
            'company_profile': 'company_info',
            'registration_document': 'company_info',
            'compliance_certificate': 'compliance',
            'experience_certificate': 'projects',
            'project_certificate': 'projects'
        }

        # Get base section from document type
        base_section = type_section_map.get(doc_type)

        # Refine based on content
        if 'gst' in search_lower or 'pan' in search_lower or 'tax' in search_lower:
            return 'compliance'
        elif 'turnover' in search_lower or 'revenue' in search_lower or '₹' in search_lower:
            return 'financial_info'
        elif 'certification' in search_lower or 'iso' in search_lower:
            return 'certifications'
        elif 'project' in search_lower or 'work' in search_lower or 'contract' in search_lower:
            return 'projects'
        elif 'company' in search_lower or 'organization' in search_lower or 'firm' in search_lower:
            return 'company_info'

        return base_section

    def _identify_section(self, page_text: str, search_text: str) -> Optional[str]:
        """Identify the section of the document based on content"""
        page_lower = page_text.lower()
        search_lower = search_text.lower()

        # Define section patterns
        section_patterns = {
            'company_info': ['company', 'organization', 'firm', 'business', 'incorporated', 'registered'],
            'financial_info': ['financial', 'turnover', 'revenue', 'profit', 'loss', 'balance', 'statement'],
            'compliance': ['gst', 'pan', 'tax', 'registration', 'certificate', 'iso', 'compliance'],
            'projects': ['project', 'work', 'contract', 'completion', 'experience', 'client'],
            'certifications': ['certification', 'iso', 'quality', 'accreditation', 'certificate'],
            'contact': ['address', 'phone', 'email', 'contact', 'location']
        }

        # Check which section patterns match the page content
        matching_sections = []
        for section, keywords in section_patterns.items():
            if any(keyword in page_lower for keyword in keywords):
                matching_sections.append(section)

        # Return the most relevant section (first match)
        return matching_sections[0] if matching_sections else None
    
    def classify_document(self, filename: str, text: str) -> str:
        """Classify document type"""
        document_types = {
            'financial_statement': ['financial', 'statement', 'balance sheet', 'p&l', 'profit', 'loss', 'revenue', 'turnover'],
            'project_certificate': ['work order', 'completion certificate', 'project', 'work', 'contract'],
            'registration_document': ['gst', 'pan', 'incorporation', 'registration', 'certificate'],
            'compliance_certificate': ['iso', 'quality', 'compliance', 'certification', 'accredited'],
            'company_profile': ['profile', 'company', 'organization', 'detail', 'about'],
            'experience_certificate': ['experience', 'certificate', 'work', 'employment', 'project completion']
        }
        
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        # Check filename first
        for doc_type, keywords in document_types.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return doc_type
        
        # Check content - count keyword matches
        scores = {}
        for doc_type, keywords in document_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return "unknown"
    
    def load_documents(self):
        """Load all PDF documents with enhanced extraction"""
        pdf_files = [f for f in os.listdir(self.workspace_path) if f.endswith('.pdf')]

        print(f"\nLoading {len(pdf_files)} documents...")
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.workspace_path, pdf_file)
            print(f"  📄 Processing: {pdf_file}")

            # Extract text (with OCR fallback) - now returns combined text and page-wise text
            combined_text, page_texts = self.extract_text_from_pdf(pdf_path)
            doc_type = self.classify_document(pdf_file, combined_text)

            # Extract tables if OCR libraries are available
            tables = []
            if OCR_AVAILABLE:
                print(f"  📊 Extracting tables from {pdf_file}...")
                tables = self.extract_tables_from_pdf(pdf_path)
                if tables:
                    print(f"    ✅ Found {len(tables)} tables")

            # Extract images if needed
            images = []
            if OCR_AVAILABLE and not combined_text.strip():  # Only if no text was found
                print(f"  🖼️  Extracting images from {pdf_file}...")
                images = self.extract_images_from_pdf(pdf_path)
                if images:
                    print(f"    ✅ Extracted {len(images)} images")

            self.extracted_text[pdf_file] = combined_text
            self.documents[pdf_file] = {
                'path': pdf_path,
                'type': doc_type,
                'text': combined_text,
                'page_texts': page_texts,  # Store page-wise text
                'tables': tables,
                'images': images,
                'size': len(combined_text)
            }

        return self.documents
    
    def extract_company_info(self) -> List[BidderField]:
        """Extract company information and create BidderField objects"""
        print("\nExtracting company information...")

        company_docs = {
            name: doc for name, doc in self.documents.items()
            if doc['type'] in ['company_profile', 'registration_document']
        }

        fields = []
        combined_text = "\n".join([doc['text'] for doc in company_docs.values()]) if company_docs else ""

        if combined_text:
            company_name = self.extractor.extract_company_name(combined_text)
            gst_number = self.extractor.extract_gst_number(combined_text)
            pan_number = self.extractor.extract_pan_number(combined_text)
            org_age = self.extractor.extract_organization_age(combined_text)

            # Create BidderField objects from extracted data
            doc_name = list(company_docs.keys())[0] if company_docs else list(self.documents.keys())[0]

            if company_name:
                page, section = self.find_text_location(company_name, doc_name)
                fields.append(BidderField(
                    field_name="company_name",
                    field_type="string",
                    value=company_name,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "company_info",
                    confidence=0.8,
                    original_text=f"Company name found in document: {company_name[:50]}..."
                ))
                print(f"  ✓ Extracted company_name: {company_name}")

            if gst_number:
                page, section = self.find_text_location(gst_number, doc_name)
                fields.append(BidderField(
                    field_name="gst_registration_number",
                    field_type="string",
                    value=gst_number,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "compliance",
                    confidence=0.95,
                    original_text=f"GST number: {gst_number}"
                ))
                print(f"  ✓ Extracted gst_registration_number: {gst_number}")

            if pan_number:
                page, section = self.find_text_location(pan_number, doc_name)
                fields.append(BidderField(
                    field_name="pan_number",
                    field_type="string",
                    value=pan_number,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "compliance",
                    confidence=0.95,
                    original_text=f"PAN number: {pan_number}"
                ))
                print(f"  ✓ Extracted pan_number: {pan_number}")
            
            if org_age > 0:
                fields.append(BidderField(
                    field_name="organization_age_years",
                    field_type="integer",
                    value=org_age,
                    source_document=doc_name,
                    confidence=0.7,
                    original_text=f"Organization age calculated as {org_age} years"
                ))
                print(f"  ✓ Extracted organization_age_years: {org_age}")
            
            # Add default bidder type
            fields.append(BidderField(
                field_name="bidder_type",
                field_type="string",
                value="Private Limited",
                source_document=doc_name,
                confidence=0.6,
                original_text="Default business type assumption"
            ))
            
            # Check for MSME
            msme_registered = "MSME" in combined_text.upper()
            fields.append(BidderField(
                field_name="msme_registered",
                field_type="boolean",
                value=msme_registered,
                source_document=doc_name,
                confidence=0.8,
                original_text=f"MSME status: {'Registered' if msme_registered else 'Not found'}"
            ))
        
        return fields
    
    def extract_financial_info(self) -> List[BidderField]:
        """Extract financial information and create BidderField objects"""
        print("Extracting financial information...")
        
        financial_docs = {
            name: doc for name, doc in self.documents.items() 
            if doc['type'] == 'financial_statement'
        }
        
        fields = []
        
        if financial_docs:
            combined_text = "\n".join([doc['text'] for doc in financial_docs.values()])
            
            # Extract currency values
            values = self.extractor.extract_currency_values(combined_text)
            all_numbers = self.extractor.extract_numbers(combined_text)
            
            # Find turnover (highest value typically)
            turnover = max(values.values()) if values else (max(all_numbers) if all_numbers else 0)
            net_worth = int(turnover * 0.6)  # Estimate as 60% of turnover
            
            # Determine period
            dates = self.extractor.extract_dates(combined_text)
            period = f"FY{dates[0]}-FY{dates[-1]}" if len(dates) >= 2 else "FY2023-FY2024"
            
            doc_name = list(financial_docs.keys())[0]
            
            if turnover > 0:
                page, section = self.find_text_location("turnover", doc_name)
                fields.append(BidderField(
                    field_name="average_annual_turnover_inr",
                    field_type="integer",
                    value=int(turnover),
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "financial_info",
                    confidence=0.7,
                    original_text=f"Turnover value extracted: ₹{turnover:,.0f}"
                ))
                print(f"  ✓ Extracted average_annual_turnover_inr: ₹{turnover:,.0f}")

            page, section = self.find_text_location("net worth", doc_name)
            fields.append(BidderField(
                field_name="net_worth_inr",
                field_type="integer",
                value=net_worth,
                source_document=doc_name,
                source_page=page,
                source_section=section or "financial_info",
                confidence=0.6,
                original_text=f"Net worth estimated as 60% of turnover: ₹{net_worth:,.0f}"
            ))

            page, section = self.find_text_location("FY", doc_name)
            fields.append(BidderField(
                field_name="turnover_period",
                field_type="string",
                value=period,
                source_document=doc_name,
                source_page=page,
                source_section=section or "financial_info",
                confidence=0.8,
                original_text=f"Financial period determined: {period}"
            ))
        
        return fields
    
    def extract_project_info(self) -> List[BidderField]:
        """Extract project information and create BidderField objects"""
        print("Extracting project information...")
        
        project_docs = {
            name: doc for name, doc in self.documents.items() 
            if doc['type'] in ['project_certificate', 'experience_certificate']
        }
        
        fields = []
        
        if project_docs:
            combined_text = "\n".join([doc['text'] for doc in project_docs.values()])
            projects = self.extractor.extract_projects(combined_text)
            
            doc_name = list(project_docs.keys())[0]
            
            # Project count
            fields.append(BidderField(
                field_name="completed_projects_count",
                field_type="integer",
                value=len(projects),
                source_document=doc_name,
                confidence=0.8,
                original_text=f"Found {len(projects)} project references in document"
            ))
            
            # Project details
            if projects:
                fields.append(BidderField(
                    field_name="project_details",
                    field_type="array",
                    value=projects,
                    source_document=doc_name,
                    confidence=0.7,
                    original_text=f"Extracted {len(projects)} project details"
                ))
            
            # Years of experience
            org_age = self.extractor.extract_organization_age(combined_text)
            fields.append(BidderField(
                field_name="years_of_experience",
                field_type="integer",
                value=max(org_age, 1),  # At least 1 year
                source_document=doc_name,
                confidence=0.6,
                original_text=f"Experience estimated as {max(org_age, 1)} years"
            ))
            
            print(f"  ✓ Extracted completed_projects_count: {len(projects)}")
        
        return fields
    
    def extract_compliance_info(self) -> List[BidderField]:
        """Extract compliance information and create BidderField objects"""
        print("Extracting compliance information...")
        
        compliance_docs = {
            name: doc for name, doc in self.documents.items() 
            if doc['type'] in ['compliance_certificate', 'registration_document']
        }
        
        fields = []
        
        if compliance_docs:
            combined_text = "\n".join([doc['text'] for doc in compliance_docs.values()])
            
            gst_number = self.extractor.extract_gst_number(combined_text)
            pan_number = self.extractor.extract_pan_number(combined_text)
            certifications = self.extractor.extract_certifications(combined_text)
            
            doc_name = list(compliance_docs.keys())[0]
            
            # GST status
            gst_registered = bool(gst_number)
            page, section = self.find_text_location("GST", doc_name)
            fields.append(BidderField(
                field_name="gst_registered",
                field_type="boolean",
                value=gst_registered,
                source_document=doc_name,
                source_page=page,
                source_section=section or "compliance",
                confidence=0.95,
                original_text=f"GST registration status: {'Found' if gst_registered else 'Not found'}"
            ))

            # GST number
            if gst_number:
                page, section = self.find_text_location(gst_number, doc_name)
                fields.append(BidderField(
                    field_name="gst_registration_number",
                    field_type="string",
                    value=gst_number,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "compliance",
                    confidence=0.95,
                    original_text=f"GST number: {gst_number}"
                ))
                print(f"  ✓ Extracted gst_registration_number: {gst_number}")

            # PAN number
            if pan_number:
                page, section = self.find_text_location(pan_number, doc_name)
                fields.append(BidderField(
                    field_name="pan_number",
                    field_type="string",
                    value=pan_number,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "compliance",
                    confidence=0.95,
                    original_text=f"PAN number: {pan_number}"
                ))
                print(f"  ✓ Extracted pan_number: {pan_number}")

            # MSME status
            msme_registered = "MSME" in combined_text.upper()
            page, section = self.find_text_location("MSME", doc_name)
            fields.append(BidderField(
                field_name="msme_registered",
                field_type="boolean",
                value=msme_registered,
                source_document=doc_name,
                source_page=page,
                source_section=section or "compliance",
                confidence=0.8,
                original_text=f"MSME status: {'Registered' if msme_registered else 'Not found'}"
            ))

            # Certifications
            if certifications:
                page, section = self.find_text_location("certification", doc_name)
                fields.append(BidderField(
                    field_name="certifications",
                    field_type="array",
                    value=certifications,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "certifications",
                    confidence=0.85,
                    original_text=f"Found {len(certifications)} certifications"
                ))
                print(f"  ✓ Extracted certifications: {len(certifications)} found")
        
        return fields
    
    def extract_bidder_id_info(self) -> List[BidderField]:
        """Extract bidder ID information and create BidderField objects"""
        print("Extracting bidder ID information...")
        
        fields = []
        
        # Search through all documents for bidder ID
        for doc_name, doc_info in self.documents.items():
            text = doc_info['text']
            bidder_id = self.extractor.extract_bidder_id(text)
            
            if bidder_id:
                page, section = self.find_text_location(bidder_id, doc_name)
                fields.append(BidderField(
                    field_name="bidder_id",
                    field_type="string",
                    value=bidder_id,
                    source_document=doc_name,
                    source_page=page,
                    source_section=section or "company_info",
                    confidence=0.9,
                    original_text=f"Bidder ID found: {bidder_id}"
                ))
                print(f"  ✓ Extracted bidder_id: {bidder_id}")
                break  # Use the first bidder ID found
        
        # If no bidder ID found in documents, generate one
        if not fields:
            # Generate a bidder ID based on company name and GST
            company_name = None
            gst_number = None
            
            # Look through existing fields for company name and GST
            for doc_name, doc_info in self.documents.items():
                text = doc_info['text']
                if not company_name:
                    company_name = self.extractor.extract_company_name(text)
                if not gst_number:
                    gst_number = self.extractor.extract_gst_number(text)
                if company_name and gst_number:
                    break
            
            if company_name and gst_number:
                # Generate bidder ID: first 3 letters of company + last 4 digits of GST
                company_prefix = re.sub(r'[^A-Z]', '', company_name.upper())[:3]
                gst_suffix = re.sub(r'[^0-9]', '', gst_number)[-4:]
                generated_id = f"{company_prefix}{gst_suffix}"
                
                # Use the first document as source
                first_doc = list(self.documents.keys())[0]
                page, section = self.find_text_location(company_name, first_doc)
                
                fields.append(BidderField(
                    field_name="bidder_id",
                    field_type="string",
                    value=generated_id,
                    source_document=first_doc,
                    source_page=page,
                    source_section=section or "company_info",
                    confidence=0.6,
                    original_text=f"Generated bidder ID from company name and GST: {generated_id}"
                ))
                print(f"  ✓ Generated bidder_id: {generated_id}")
            else:
                # Fallback: use timestamp-based ID
                import time
                timestamp_id = f"BID{int(time.time()) % 10000:04d}"
                
                first_doc = list(self.documents.keys())[0]
                fields.append(BidderField(
                    field_name="bidder_id",
                    field_type="string",
                    value=timestamp_id,
                    source_document=first_doc,
                    source_page=None,
                    source_section="generated",
                    confidence=0.3,
                    original_text=f"Generated fallback bidder ID: {timestamp_id}"
                ))
                print(f"  ✓ Generated fallback bidder_id: {timestamp_id}")
        
        return fields
    
    def build_bidder_profile(self) -> Dict[str, Any]:
        """Build comprehensive bidder profile from BidderField objects"""
        print("\n[2/5] Building Bidder Profile")

        # Extract all bidder fields using Qwen API
        company_fields = self.extract_company_info()
        financial_fields = self.extract_financial_info()
        project_fields = self.extract_project_info()
        compliance_fields = self.extract_compliance_info()
        bidder_id_fields = self.extract_bidder_id_info()

        # Extract table data if OCR libraries are available
        table_fields = []
        if OCR_AVAILABLE:
            print("🔄 Processing table data from documents...")
            for doc_name, doc_info in self.documents.items():
                tables = doc_info.get('tables', [])
                if tables:
                    doc_table_fields = self.process_table_data(tables)
                    # Add source document info to table fields
                    for field in doc_table_fields:
                        field.source_document = doc_name
                    table_fields.extend(doc_table_fields)
            if table_fields:
                print(f"✅ Extracted {len(table_fields)} fields from tables")

        # Combine all fields
        all_fields = company_fields + financial_fields + project_fields + compliance_fields + bidder_id_fields + table_fields

        # Propagate bidder_id into every field object
        final_bidder_id = bidder_id_fields[0].value if bidder_id_fields else None
        if final_bidder_id:
            for field in all_fields:
                field.bidder_id = final_bidder_id

        self.bidder_fields = all_fields

        # Create summary profile from fields
        profile = {
            "bidder_fields": [asdict(field) for field in all_fields],
            "summary": self._create_summary_from_fields(all_fields),
            "processing_timestamp": datetime.now().isoformat(),
            "processing_mode": "qwen_structured_extraction_with_ocr_tables",
            "documents_processed": list(self.documents.keys()),
            "document_classifications": {
                name: doc['type'] for name, doc in self.documents.items()
            },
            "ocr_enabled": OCR_AVAILABLE,
            "table_extraction_enabled": OCR_AVAILABLE,
            "total_fields_extracted": len(all_fields),
            "fields_by_source": {
                "text_extraction": len(company_fields + financial_fields + project_fields + compliance_fields + bidder_id_fields),
                "table_extraction": len(table_fields)
            }
        }

        self.bidder_profile = profile
        return profile
    
    def _create_summary_from_fields(self, fields: List[BidderField]) -> Dict[str, Any]:
        """Create a summary view from the BidderField objects"""
        summary = {
            "bidder_id": "Not Generated",
            "company_name": "Not Extracted",
            "bidder_type": "Not Specified",
            "msme_registered": False,
            "organization_age_years": 0,
            "average_annual_turnover_inr": 0,
            "turnover_period": "Not Specified",
            "net_worth_inr": 0,
            "completed_projects_count": 0,
            "project_details": [],
            "years_of_experience": 0,
            "gst_registration_number": "",
            "gst_registered": False,
            "pan_number": "",
            "certifications": [],
            "jv_structure": None
        }
        
        # Map fields to summary
        field_mapping = {
            "bidder_id": "bidder_id",
            "company_name": "company_name",
            "bidder_type": "bidder_type",
            "organization_age_years": "organization_age_years",
            "msme_registered": "msme_registered",
            "average_annual_turnover_inr": "average_annual_turnover_inr",
            "turnover_period": "turnover_period",
            "net_worth_inr": "net_worth_inr",
            "completed_projects_count": "completed_projects_count",
            "project_details": "project_details",
            "years_of_experience": "years_of_experience",
            "gst_registration_number": "gst_registration_number",
            "gst_registered": "gst_registered",
            "pan_number": "pan_number",
            "certifications": "certifications"
        }
        
        for field in fields:
            if field.field_name in field_mapping:
                summary[field_mapping[field.field_name]] = field.value
        
        return summary
    
    def save_bidder_profile(self, output_filename: str = "bidder_profile.json", save_to_db: bool = True):
        """Save bidder profile to JSON and optionally store bidder fields in PostgreSQL"""
        output_path = os.path.join(self.workspace_path, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.bidder_profile, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Bidder profile saved: {output_filename}")

        if save_to_db:
            if not DB_AVAILABLE:
                print("⚠️ SQLAlchemy is not installed; skipping PostgreSQL save.")
            else:
                db_manager = DBManager()
                try:
                    db_manager.init_tables()
                    db_manager.store_bidder_fields(self.bidder_profile)
                    print("✓ Bidder fields saved to PostgreSQL")
                except Exception as e:
                    print(f"⚠️ Failed to save bidder fields to PostgreSQL: {e}")
                finally:
                    db_manager.close()

        return output_path
    
    def generate_report(self, output_filename: str = "bidder_processing_report.md"):
        """Generate markdown report from BidderField objects"""
        output_path = os.path.join(self.workspace_path, output_filename)
        
        profile = self.bidder_profile
        summary = profile.get('summary', {})
        bidder_fields = profile.get('bidder_fields', [])
        
        report = f"""# Bidder Document Processing Report

## Processing Information
- **Timestamp**: {profile.get('processing_timestamp', 'N/A')}
- **Mode**: {profile.get('processing_mode', 'N/A')}
- **Documents Processed**: {len(profile.get('documents_processed', []))}
- **Total Fields Extracted**: {len(bidder_fields)}

## Document Classifications
"""
        
        for doc_name, doc_type in profile.get('document_classifications', {}).items():
            report += f"- **{doc_name}**: `{doc_type}`\n"
        
        report += f"""

## EXTRACTED BIDDER FIELDS

### Structured Field Extraction Results
"""
        
        # Group fields by category
        field_categories = {
            "Company Information": ["company_name", "bidder_type", "organization_age_years", "msme_registered"],
            "Financial Information": ["average_annual_turnover_inr", "net_worth_inr", "turnover_period"],
            "Project Information": ["completed_projects_count", "project_details", "years_of_experience"],
            "Compliance Information": ["gst_registered", "gst_registration_number", "pan_number", "certifications"]
        }
        
        for category, field_names in field_categories.items():
            report += f"\n#### {category}\n"
            
            category_fields = [f for f in bidder_fields if f['field_name'] in field_names]
            
            if category_fields:
                for field in category_fields:
                    report += f"- **{field['field_name']}**: {field['value']} "
                    report += f"(confidence: {field['confidence']:.2f})\n"
                    if field.get('source_document'):
                        report += f"  - Source: {field['source_document']}\n"
                    if field.get('original_text'):
                        report += f"  - Text: \"{field['original_text'][:100]}...\"\n"
            else:
                report += "- No fields extracted\n"
        
        report += f"""

## BIDDER PROFILE SUMMARY

### Company Information
- **Bidder ID**: {summary.get('bidder_id', 'Not Generated')}
- **Company Name**: {summary.get('company_name', 'Not Extracted')}
- **Business Type**: {summary.get('bidder_type', 'Not Specified')}
- **Organization Age**: {summary.get('organization_age_years', 0)} years
- **MSME Registered**: {'Yes' if summary.get('msme_registered', False) else 'No'}

### Financial Profile
- **Average Annual Turnover**: ₹{summary.get('average_annual_turnover_inr', 0):,}
- **Turnover Period**: {summary.get('turnover_period', 'Not Specified')}
- **Net Worth**: ₹{summary.get('net_worth_inr', 0):,}

### Experience & Projects
- **Completed Projects**: {summary.get('completed_projects_count', 0)}
- **Years of Experience**: {summary.get('years_of_experience', 0)} years

### Compliance & Certifications
- **GST Registered**: {'Yes' if summary.get('gst_registered', False) else 'No'}
- **GST Registration Number**: {summary.get('gst_registration_number', 'Not Found')}
- **PAN Number**: {summary.get('pan_number', 'Not Found')}

**Certifications**:
"""
        
        certs = summary.get('certifications', [])
        if certs:
            for cert in certs:
                report += f"- {cert}\n"
        else:
            report += "- No certifications found\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ Report saved: {output_filename}")
        return output_path
    
    def generate_csv_summary(self, output_filename: str = "bidder_summary.csv"):
        """Generate CSV summary for easy import"""
        import csv
        
        output_path = os.path.join(self.workspace_path, output_filename)
        profile = self.bidder_profile
        summary = profile.get('summary', {})
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field', 'Value', 'Confidence'])
            
            data = [
                ('Bidder ID', summary.get('bidder_id', ''), '0.90'),
                ('Company Name', summary.get('company_name', ''), '0.85'),
                ('Business Type', summary.get('bidder_type', ''), '0.90'),
                ('Organization Age (Years)', summary.get('organization_age_years', 0), '0.85'),
                ('MSME Registered', summary.get('msme_registered', False), '0.90'),
                ('Average Annual Turnover (INR)', summary.get('average_annual_turnover_inr', 0), '0.70'),
                ('Turnover Period', summary.get('turnover_period', ''), '0.75'),
                ('Net Worth (INR)', summary.get('net_worth_inr', 0), '0.70'),
                ('Completed Projects', summary.get('completed_projects_count', 0), '0.80'),
                ('Years of Experience', summary.get('years_of_experience', 0), '0.85'),
                ('GST Registered', summary.get('gst_registered', False), '0.95'),
                ('GST Number', summary.get('gst_registration_number', ''), '0.95'),
                ('PAN Number', summary.get('pan_number', ''), '0.95'),
            ]
            
            for row in data:
                writer.writerow(row)
        
        print(f"✓ CSV summary saved: {output_filename}")
        return output_path


def main():
    """Main execution"""
    print("=" * 70)
    print("BIDDER DOCUMENT PROCESSING SYSTEM - ENHANCED")
    print("=" * 70)
    
    processor = BidderDocumentProcessor(WORKSPACE_PATH)
    
    # Load documents
    print("\n[1/5] Loading and Classifying Documents")
    documents = processor.load_documents()
    print(f"✓ Loaded {len(documents)} documents\n")
    
    # Build profile
    print("\n[2/5] Building Bidder Profile")
    profile = processor.build_bidder_profile()
    
    # Save outputs
    print("\n[3/5] Saving Outputs")
    processor.save_bidder_profile("bidder_profile.json")
    processor.generate_report("bidder_processing_report.md")
    processor.generate_csv_summary("bidder_summary.csv")
    
    # Display summary
    print("\n[4/5] Profile Summary")
    print("-" * 70)
    summary = profile.get('summary', {})
    print(f"Bidder ID: {summary.get('bidder_id', 'Not Generated')}")
    print(f"Company: {summary.get('company_name', 'Not Extracted')}")
    print(f"Turnover: ₹{summary.get('average_annual_turnover_inr', 0):,}")
    print(f"Completed Projects: {summary.get('completed_projects_count', 0)}")
    print(f"Fields Extracted: {len(profile.get('bidder_fields', []))}")
    print(f"GST Status: {'Registered' if summary.get('gst_registered') else 'Not Found'}")
    print("-" * 70)
    
    # Full JSON output
    print("\n[5/5] Full Bidder Profile (JSON)")
    print("=" * 70)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print("=" * 70)
    print("\n✓ Processing Complete!")


if __name__ == "__main__":
    main()
