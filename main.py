from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

from Config import Headers, Soap_url, Attrib, REST_API, METHOD

app = Flask(__name__)

@app.route(REST_API, methods=[METHOD])
def convert_rest_to_soap():
    rest_request = request.json
    print(Fore.MAGENTA + "-----------------------------------------------------------------------------------------------")
    print(Fore.CYAN + "Postman given REST Request:" + str(rest_request))
    print(Fore.GREEN + "REST Request received")
    # print("Postman given REST Request:")
    # print(rest_request)

    # Convert REST request to SOAP request
    soap_request = build_soap_request(rest_request)
    print(Fore.GREEN + "REST request converted to SOAP request")
    # print("Converted SOAP Request:")
    # print(soap_request)

    # Send SOAP request to SOAP server
    soap_response = send_soap_request(soap_request)
    print(Fore.GREEN + "SOAP Response received ")
    # print("SOAP Response:")
    # print(soap_response)

    # Convert SOAP response to REST response
    rest_response = convert_soap_to_rest_response(soap_response)
    print(Fore.GREEN + "SOAP Response converted to REST Response")
    # print("Converted REST Response:")
    # print(rest_response)

    print(Fore.GREEN + "Send to REST Response")
    return jsonify(rest_response)


# Convert REST Request to SOAP Request
def build_soap_request(rest_request):
    envelope = ET.Element('soapenv:Envelope', attrib=Attrib)
    body = ET.SubElement(envelope, 'soapenv:Body')

    if rest_request['action'] == 'create':
        request_element = ET.SubElement(body, 'ns:create_student')
        ET.SubElement(request_element, 'ns:name').text = rest_request['name']
        ET.SubElement(request_element, 'ns:description').text = rest_request['description']

    elif rest_request['action'] == 'read_all':
        ET.SubElement(body, 'ns:read_student')

    elif rest_request['action'] == 'read_by_id':
        request_element = ET.SubElement(body, 'ns:read_student_by_id')
        ET.SubElement(request_element, 'ns:student_id').text = str(rest_request['student_id'])

    elif rest_request['action'] == 'update':
        request_element = ET.SubElement(body, 'ns:update_item')
        ET.SubElement(request_element, 'ns:student_id').text = str(rest_request['student_id'])
        ET.SubElement(request_element, 'ns:name').text = rest_request['name']
        ET.SubElement(request_element, 'ns:description').text = rest_request['description']

    elif rest_request['action'] == 'delete':
        request_element = ET.SubElement(body, 'ns:delete_item')
        ET.SubElement(request_element, 'ns:student_id').text = str(rest_request['student_id'])

    return ET.tostring(envelope, encoding='utf-8', method='xml').decode()

# Send SOAP request to SOAP server
def send_soap_request(soap_request):
    soap_url = Soap_url
    headers = Headers
    response = requests.post(soap_url, data=soap_request, headers=headers)
    return response.text


def convert_soap_to_rest_response(soap_response):
    # Parse the SOAP response XML
    root = ET.fromstring(soap_response)
    response_data = {}

    # Define the namespaces used in the SOAP response
    namespaces = {
        'soap11env': 'http://schemas.xmlsoap.org/soap/envelope/',
        'tns': 'soap_app.ItemService'
    }

    # Handle 'create_student' SOAP response
    if 'create_student' in soap_response:
        result_element = root.find('.//tns:create_studentResult', namespaces)
        if result_element is not None and result_element.text:
            response_data['message'] = "Student created successfully."
            response_data['details'] = {
                "ID": int(result_element.text.split()[-1]),  # Extract ID from message
                "Name": result_element.text.split()[1],  # Extract Name from message
                "status": result_element.text
            }
        else:
            response_data['message'] = "Student creation failed."

    # Handle 'update_item' SOAP response
    elif 'update_item' in soap_response:
        result_element = root.find('.//tns:update_itemResult', namespaces)
        if result_element is not None and 'updated' in result_element.text:
            # Extract the student ID from the message
            student_id = result_element.text.split()[1]  # The ID is after the word "Item"
            response_data['message'] = "Student updated successfully."
            response_data['details'] = {
                "ID": int(student_id),  # Convert extracted ID to integer
                "status": result_element.text
            }
        else:
            response_data['message'] = "Student update failed."
            response_data['error'] = {
                "status": result_element.text if result_element is not None else "No response"
            }

    # Handle 'delete_item' SOAP response
    elif 'delete_item' in soap_response:
        result_element = root.find('.//tns:delete_itemResult', namespaces)
        if result_element is not None and 'deleted' in result_element.text:
            response_data['message'] = "Student deleted successfully."
            response_data['details'] = {
                "ID": int(result_element.text.split()[1]),  # Extract ID from message
                "status": result_element.text
            }
        else:
            response_data['message'] = "Student deletion failed."

    # Handle 'read_student_by_id' SOAP response
    elif 'read_student_by_id' in soap_response:
        result_element = root.find('.//tns:read_student_by_idResult', namespaces)
        if result_element is not None:
            student_data = result_element.text  # The result is a string like "ID: 3, Name: John Doe, Description: A new student"

            # Check if the response indicates that the student was not found
            if 'not found' in student_data:
                student_id = student_data.split()[3]  # Extract the ID from the message
                response_data['message'] = "Student not found."
                response_data['error'] = {
                    "ID": student_id,  # Keep it as a string since it's part of the error message
                    "status": student_data
                }
            else:
                # Split the result by commas to get individual fields
                fields = student_data.split(', ')
                student = {}

                # Parse the individual fields and add them to the student dictionary
                for field in fields:
                    if ': ' in field:
                        key, value = field.split(': ')
                        student[key] = value

                response_data['message'] = "Student data found."
                response_data['student'] = {
                    "ID": int(student.get("ID")),
                    "Name": student.get("Name"),
                    "Description": student.get("Description")
                }
        else:
            response_data['message'] = "Student not found."

    # Handle 'read_student' (read all) SOAP response
    elif 'read_student' in soap_response:
        result_element = root.find('.//tns:read_studentResult', namespaces)
        response_data['students'] = []
        if result_element is not None and result_element.text:
            # Split the message by newline to separate each student
            students_data = result_element.text.strip().split('\n')

            for student_info in students_data:
                # Split each student's details by comma
                student_fields = student_info.split(', ')
                student = {}

                # Extract each field and populate the student dictionary
                for field in student_fields:
                    key, value = field.split(': ')
                    student[key] = value

                # Append the structured student data to the response
                response_data["students"].append({
                    "ID": int(student.get("ID")),
                    "Name": student.get("Name"),
                    "Description": student.get("Description")
                })
        else:
            response_data['message'] = "No students found."

    # Default case if no action matches
    else:
        response_data['message'] = "No result found in the SOAP response or the response format doesn't match."

    return response_data


if __name__ == '__main__':
    app.run(debug=True, port=5001)
