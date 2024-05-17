import requests
from bs4 import BeautifulSoup
import dns.resolver
import socket
import whois
import re
import openpyxl

class SubdomainEnumerator:
    def __init__(self, target_domain, wordlist_file, common_ports):
        self.target_domain = target_domain
        self.wordlist_file = wordlist_file
        self.common_ports = common_ports
        self.emails = []
        self.excel_data = []

    def enumerate_subdomains(self):
        with open(self.wordlist_file, 'r') as f:
            for line in f:
                subdomain = line.strip()
                domain = subdomain + '.' + self.target_domain
                try:
                    answers = dns.resolver.resolve(domain, 'A')
                    for answer in answers:
                        ipaddress = str(answer)
                        open_ports = []
                        for port in self.common_ports:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1) 
                            result = sock.connect_ex((ipaddress, port))
                            if result == 0:
                                open_ports.append(port)
                            sock.close()

                        if open_ports:
                            print("------------------------------------------------------------")
                            print(f"Subdomain: {subdomain}")
                            print(f"IP Address: {ipaddress}")
                            print(f"Open Ports: {', '.join(map(str, open_ports))}")
                            print(f"URL: http://{subdomain}.{self.target_domain}")
                            print("------------------------------------------------------------")
                            self.excel_data.append(['Subdomain', subdomain])
                            self.excel_data.append(['IP Address', ipaddress])
                            self.excel_data.append(['Open Ports', ', '.join(map(str, open_ports))])
                            self.excel_data.append(['URL', f"http://{subdomain}.{self.target_domain}"])
                            self.scrape_links(subdomain)
                except dns.resolver.NXDOMAIN:
                    pass
                except dns.resolver.NoAnswer:
                    pass
                except dns.resolver.Timeout:
                    pass
                except Exception as e:
                    print(f"Error occurred: {e}")

        self.finalize_operations()

    def scrape_links(self, subdomain):
        url = f'http://{subdomain}.{self.target_domain}'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            print(f"Title: {title}")
            self.excel_data.append(['Title', title])
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                title = link.get_text().strip()
                if href and href.startswith('http'):
                    status = requests.head(href).status_code
                    print(f"Link: {href}")
                    print(f"Title: {title}")
                    print(f"Status Code: {status}")
                    self.excel_data.append(['Link', href])
                    self.excel_data.append(['Title', title])
                    self.excel_data.append(['Status Code', status])
                elif href and href.startswith('mailto:'):
                    email = href.replace('mailto:', '')
                    print(f"Extracted Email: {email}")
                    self.emails.append(email)
        else:
            print(f"Failed to retrieve the page for {subdomain}.{self.target_domain}")

    def get_whois_info(self, domain):
        try:
            w = whois.whois(domain)
            print(f"WHOIS Info: {w}")
            self.excel_data.append(['WHOIS Info', str(w)])
        except Exception as e:
            print(f"Error getting WHOIS info: {e}")

    def finalize_operations(self):
        self.extract_emails()
        self.get_whois_info(self.target_domain)
        self.extract_contacts_from_website()
        self.write_to_excel()

    def extract_emails(self):
        if not self.emails:
            print("No emails were extracted.")
        else:
            for email in self.emails:
                print(f"Extracted Email: {email}")
                self.excel_data.append(['Extracted Email', email])

    def write_to_excel(self):
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Subdomain Info"

        for row in self.excel_data:
            sheet.append(row)

        excel_file = f"{self.target_domain}_info.xlsx"
        wb.save(excel_file)
        print(f"Excel file saved: {excel_file}")

    def extract_contacts_from_website(self):
        emails, phone_numbers, phone_numbers1 = extract_contacts_from_website(self.target_domain)
        for email in emails:
            print(f"Extracted Email: {email}")
            self.excel_data.append(['Extracted Email', email])
        for number in phone_numbers:
            print(f"Phone Number: {number}")
            self.excel_data.append(['Phone Number', number])
        for number in phone_numbers1:
            print(f"Phone Number: {number}")
            self.excel_data.append(['Phone Number', number])

def extract_contacts_from_website(target_domain):
    url = f"https://{target_domain}"
    response = requests.get(url)
    if response.status_code == 200:
        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', response.text)
        phone_numbers = re.findall(r"021-\d{8}", response.text)
        phone_numbers1 = re.findall(r"021\d{8}", response.text)
        return emails, phone_numbers, phone_numbers1
    else:
        print("Failed to retrieve the website content.")
        return [], [], []

if __name__ == '__main__':
    target_domain = input("Enter the target domain: ")
    wordlist_file = 'wordlist.txt'
    common_ports = [21, 22, 23, 25, 53, 80, 110, 119, 123, 143, 161, 194, 443, 445, 993, 995, 3306]
    
    enumerator = SubdomainEnumerator(target_domain, wordlist_file, common_ports)
    enumerator.enumerate_subdomains()
