
import stardog

from core.consts.configure import DATASOURCE_YML_CONFIG_FILE
from core.consts.database import STARDOG_CONN_DETAILS
from core.data_reformat.ontology_xml_handler import OntologyXMLResultHandler


class StardogDatabase:

    def get_query(self,spqrql,prefix):
        conn = stardog.Connection(DATASOURCE_YML_CONFIG_FILE["database"]["stardog"]["db"], **STARDOG_CONN_DETAILS)

        results = conn.select(spqrql, content_type='application/sparql-results+xml')

        return results

    def pred_query(self,query, prefix):
        # 临时Ontology查询
        warning_sign_sparql = "SELECT ?hazard WHERE { :" + query + " :isWarningSignFor ?hazard }"
        ontology_res = self.get_query(warning_sign_sparql, "PREFIX : " + prefix)

        # 进行XML反解析

        dict = OntologyXMLResultHandler.xml_to_dict(ontology_res)

        return OntologyXMLResultHandler.get_uri_val(dict)