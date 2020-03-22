import xmltodict


'''
    依赖包下载
    pip install xmltodict
'''


class OntologyXMLResultHandler:
    @classmethod
    def xml_to_dict(cls,context):
        res = xmltodict.parse(context)
        return res

    @classmethod
    def get_uri_val(cls,value):

        res = []

        for val in value["sparql"]["results"]["result"]:
            res.append(val["binding"]["uri"].split('#')[1])

        return res
