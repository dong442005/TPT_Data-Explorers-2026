import os
import re

def get_page_count(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
            # Simple regex to count /Page occurrences in PDF
            return len(re.findall(b'/Type\\s*/Page[^s]', content))
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    v = get_page_count("docs/reports/technical_report/technical_report_vi.pdf")
    e = get_page_count("docs/reports/technical_report/technical_report_en.pdf")
    print(f"VI pages: {v}")
    print(f"EN pages: {e}")
