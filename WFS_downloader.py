import requests
import xml.dom.minidom
# from tqdm import tqdm
    
base_url = "https://inspire-hessen.de/ows/services/org.2.e305d5c1-54e3-4ef4-b0a1-527237ac7bfa_wfs?"
layer_name = "cp:CadastralParcel"
output_path = r"C:\DVP_Projects\data\resultWfsAllPages_v110_withTrue.gml"
# total_pages_to_fetch = 25000

request_size = requests.get(base_url , params={
    "service": "WFS",
    "request": "getcapabilities"
})
request_size_parse = xml.dom.minidom.parseString(request_size.content)
constraint_elements = request_size_parse.getElementsByTagName('ows:Constraint')
for element in constraint_elements :
    if element.getAttribute("name") == "CountDefault":
        default_value = element.getElementsByTagName("ows:DefaultValue")[0]
        batch_size = int(default_value.firstChild.nodeValue)
#print(batch_size)

# Calculate the number of pages for the resquest:
request_hits = requests.get(base_url , params={
    "service": "WFS",
    "version": "1.1.0",
    "request": "GetFeature",
    "typeName": layer_name,
    "outputFormat": "application/gml+xml; version=3.2",
    "resultType":"hits"
})
print(request_hits.text)
result_parse = xml.dom.minidom.parseString(request_hits.content)
result_fc = result_parse.getElementsByTagName("wfs:FeatureCollection")
total_hits = int(result_fc[0].getAttribute("numberOfFeatures"))
total_pages = (total_hits + batch_size - 1) // batch_size
# print(f"Total features: {total_hits}, " f"Total pages: {total_pages}")

# Open the output file for writing in append mode
output_file = open(output_path, "wb")

# Call GetFeature once to fetch the GML header
params1 = {
    "service": "WFS",
    "version": "1.1.0",
    "request": "GetFeature",
    "typeName": layer_name,
    "maxFeatures":"1",
    "outputFormat": "application/gml+xml; version=3.2",
}
response_header = requests.get(base_url, params=params1)
header = response_header.text.split("<gml:featureMember>")[0]
# Write the header in the opened document:
output_file.write(header.encode('utf-8'))

# Loop through the pages and fetch only the elements that represent the actual features (exclude each page header)
start_index = 0
while start_index < total_hits : 
    params2 = {
        "service": "WFS",
        "version": "1.1.0", 
        "request": "GetFeature",
        "typeName": layer_name,
        "startIndex": start_index,
        "maxFeatures": batch_size,
        "outputFormat": "application/gml+xml; version=3.2",
        # "sortBy" : "nationalCadastralReference", (Not working in some WFS)
}
    response = requests.get(base_url, params=params2, stream=False)
        # with requests.get(base_url, params=params2, stream=True) as response: # Another way to get response
    # Parse xml reponse 
    root = xml.dom.minidom.parseString(response.content)
    # Find all featureCollection elements
    feature_collections = root.getElementsByTagName("gml:FeatureCollection")
    for feature_collection in feature_collections:
        #print(f"feature collection: {feature_collection}")
        # Find and Append each featureMember element to the output file
        feature_members = feature_collection.childNodes
        for feature_member in feature_members:
            output_file.write(feature_member.toxml().encode('utf-8')) # write the element in the outputfile
            #print(feature_member.toxml(), file=output_file)
    start_index += batch_size
            
# Close the GML file with the closing tag
closing_gml = "\n</gml:FeatureCollection>"
output_file.write(closing_gml.encode('utf-8'))

# Close the document
output_file.close()
