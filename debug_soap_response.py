#!/usr/bin/env python3
"""
Debug script to examine the SOAP response structure
"""

import xml.etree.ElementTree as ET

# Sample response from the logs
response_text = '''<?xml version="1.0"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:NS1="urn:BPMServicesIntf-IBPMServices"><NS1:AtenderMensajeRNDCResponse><return xsi:type="xsd:string">&lt;?xml version="1.0" encoding="ISO-8859-1" ?&gt;
&lt;root&gt;
&lt;ErrorMSG&gt;NO SE ENCONTRO INFORMACION&lt;/ErrorMSG&gt;
&lt;/root&gt;</return></NS1:AtenderMensajeRNDCResponse></SOAP-ENV:Body></SOAP-ENV:Envelope>'''

print("Parsing SOAP response...")
root = ET.fromstring(response_text)
print(f"Root tag: {root.tag}")

# Find all elements recursively
def print_element_tree(elem, indent=0):
    print("  " * indent + f"{elem.tag}")
    if elem.text and elem.text.strip():
        text_preview = elem.text.strip()[:100]
        print("  " * indent + f"  TEXT: {text_preview}...")
    for child in elem:
        print_element_tree(child, indent + 1)

print("\nElement tree:")
print_element_tree(root)

# Try to find the return element
print("\n" + "="*60)
print("Looking for return element...")

# Method 1: Direct search
return_elem = root.find('.//return')
if return_elem is not None:
    print("Found with direct search!")
    print(f"Return text: {return_elem.text[:200] if return_elem.text else 'None'}")

# Method 2: With namespace
for namespace in [
    '{urn:BPMServicesIntf-IBPMServices}',
    '{http://schemas.xmlsoap.org/soap/envelope/}',
    '{http://schemas.xmlsoap.org/soap/encoding/}'
]:
    return_elem = root.find(f'.//{namespace}return')
    if return_elem is not None:
        print(f"Found with namespace: {namespace}")
        print(f"Return text: {return_elem.text[:200] if return_elem.text else 'None'}")
        break

# Method 3: Iterate through all elements
print("\nAll elements with 'return' in tag:")
for elem in root.iter():
    if 'return' in elem.tag.lower():
        print(f"  Tag: {elem.tag}")
        print(f"  Text: {elem.text[:200] if elem.text else 'None'}")

# Parse the inner XML
print("\n" + "="*60)
print("Parsing inner XML...")

# Find return element without namespace
body = None
for elem in root:
    if 'Body' in elem.tag:
        body = elem
        break

if body:
    print(f"Found body: {body.tag}")
    for child in body:
        print(f"  Body child: {child.tag}")
        if 'Response' in child.tag:
            for subchild in child:
                print(f"    Response child: {subchild.tag}")
                if 'return' in subchild.tag.lower():
                    inner_xml = subchild.text
                    print(f"\nInner XML found!")
                    print(f"Inner XML: {inner_xml}")

                    # Parse the inner XML
                    try:
                        inner_root = ET.fromstring(inner_xml)
                        print(f"\nInner root tag: {inner_root.tag}")

                        error_node = inner_root.find("ErrorMSG")
                        if error_node is not None:
                            print(f"ERROR MESSAGE: {error_node.text}")
                    except Exception as e:
                        print(f"Failed to parse inner XML: {e}")