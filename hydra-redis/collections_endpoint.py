import urllib.request
import json
import re
from classes_objects import ClassEndpoints


class CollectionEndpoints:
    """Contains all the collections endpoints and objects"""

    def __init__(self, redis_graph, class_endpoints):
        self.redis_graph = redis_graph
        self.class_endpoints = class_endpoints

    def fetch_data(self, new_url):
        """Fetching data from the server"""
        response = urllib.request.urlopen(new_url)
        return json.loads(response.read().decode('utf-8'))

    def collectionobjects(
            self,
            endpoint_collection_node,
            endpoint_list,
            new_url,
            entrypoint_node,
            api_doc,
            url):
        """Creating nodes for all objects stored in collection."""
        print("accesing the collection object like events or drones")
        if endpoint_list:
            clas = ClassEndpoints(self.redis_graph)
            for endpoint in endpoint_list:
                node_properties = {}
                no_endpoint_property = []
                endpoint_method = []
                member = {}
                endpoint_property_list = []
                supported_property_list = []
                match_obj = re.match(
                    r'/(.*)/(.*)/(.*)?', endpoint["@id"], re.M | re.I)
                base_url = "/{0}/{1}/".format(match_obj.group(1),
                                              match_obj.group(2))
                entrypoint_member = endpoint["@type"].lower(
                ) + match_obj.group(3)
                print(base_url, entrypoint_member)
                member_alias = entrypoint_member
                # key for the object node is memeber_alias
                member_id = match_obj.group(3)
                print("member alias and id", member_alias, member_id)
                new_url1 = new_url + "/" + member_id
                new_file1 = self.fetch_data(new_url1)
                # object data retrieving from the server
                for support_operation in api_doc.parsed_classes[
                                                      endpoint["@type"]
                                                      ]["class"
                                                        ].supportedOperation:
                    endpoint_method.append(support_operation.method)
                node_properties["operations"] = str(endpoint_method)
                # all the operations for the object is stored in method
                for support_property in api_doc.parsed_classes[
                                                      endpoint["@type"]
                                                      ]["class"
                                                        ].supportedProperty:
                    supported_property_list.append(support_property.title)
                    if support_property.title in self.class_endpoints:
                        endpoint_property_list.append(
                            str(support_property.title))
                    elif support_property.title in api_doc.parsed_classes:
                        no_endpoint_property.append(support_property.title)

                    if isinstance(new_file1[support_property.title], str):
                        if support_property.title in new_file1:
                            member[support_property.title] = str(
                                new_file1[
                                    support_property.title].replace(" ", ""))
                        else:
                            member[support_property.title] = "null"
                no_endpoint_list = no_endpoint_property
                # all property which itself is an object

                node_properties["@id"] = str(endpoint["@id"])
                node_properties["@type"] = str(endpoint["@type"])
                node_properties["property_value"] = str(member)
                node_properties["properties"] = str(supported_property_list)
                collection_object_node = clas.addNode(
                    "objects", str(member_alias), node_properties)
                # add object as a node in redis
                clas.addEdge(endpoint_collection_node, "has_" +
                             str(endpoint["@type"]), collection_object_node)
                # set an edge between the collection and its object
                print(
                    "property of endpoint which can be class but not endpoint",
                    no_endpoint_list
                )
                if endpoint_property_list:
                    for endpoint_property in endpoint_property_list:
                        for nodes in self.redis_graph.nodes.values():
                            if endpoint_property == nodes.alias:
                                clas.addEdge(
                                    collection_object_node,
                                    "hasendpointproperty",
                                    nodes)
                if no_endpoint_list:
                    clas.objects_property(
                        collection_object_node,
                        no_endpoint_list,
                        entrypoint_node,
                        api_doc)
        else:
            print("NO MEMBERS")

    def endpointCollection(
            self,
            collection_endpoint,
            entrypoint_node,
            api_doc,
            url):
        """It makes a node for every collection endpoint."""
        print("accessing every collection in entrypoint")
        clas = ClassEndpoints(self.redis_graph)
        for endpoint in collection_endpoint:
            endpoint_method = []
            node_properties = {}
            print(
                "check url for endpoint",
                url +
                collection_endpoint[endpoint].replace("vocab:EntryPoint", ""))
            new_url = url + \
                collection_endpoint[endpoint].replace("vocab:EntryPoint", "")
            # url for every collection endpoint
            for support_operation in api_doc.collections[
                    endpoint][
                    "collection"].supportedOperation:
                endpoint_method.append(support_operation.method)
            node_properties["operations"] = str(endpoint_method)
            # all the operations for the collection endpoint is stored in
            print("supportedOperations",node_properties["operations"])
            node_properties["@id"] = str(collection_endpoint[endpoint])
            new_file = self.fetch_data(new_url)
            # retrieving the objects from the collection endpoint
            node_properties["members"] = str(new_file["members"])
            endpoint_collection_node = clas.addNode(
                "collection", endpoint, node_properties)
            clas.addEdge(
                entrypoint_node,
                "has_collection",
                endpoint_collection_node)
            # set an edge between the entrypoint and collection endpoint
            self.collectionobjects(
                endpoint_collection_node,
                new_file["members"],
                new_url,
                entrypoint_node,
                api_doc,
                url
            )
