import yaml
import random
import string
import dicttoxml2

from bbot.modules.base import BaseModule


class openapi(BaseModule):
    watched_events = ["URL"]
    produced_events = ["URL", "HTTP_RESPONSE"]
    flags = ["active", "web-thorough"]
    meta = {"description": "Parses OpenAPI specifications from any detected URLs"}

    deps_pip = ["dicttoxml2"]

    in_scope_only = True

    async def setup(self):
        self.openapi_paths = [
            "/swagger.json",
            "/swagger.yaml",
            "/swagger.yml",
            "/api-docs/swagger.json",
            "/api-docs/swagger.yaml",
            "/api-docs/swagger.yml",
            "/api-docs/v1/swagger.json",
            "/api-docs/v1/swagger.yaml",
            "/api-docs/v1/swagger.yml",
            "/swagger/v1/swagger.json",
            "/swagger/v1/swagger.yaml",
            "/swagger/v1/swagger.yml",
            "/api/swagger.json",
            "/api/swagger.yaml",
            "/api/swagger.yml",
            "/api/api-docs/swagger.json",
            "/api/api-docs/swagger.yaml",
            "/api/api-docs/swagger.yml",
            "/api/swagger-ui/swagger.json",
            "/api/swagger-ui/swagger.yaml",
            "/api/swagger-ui/swagger.yml",
            "/api/apidocs/swagger.json",
            "/api/apidocs/swagger.yaml",
            "/api/apidocs/swagger.yml",
            "/api/doc.json",
            "/api/spec/swagger.json",
            "/api/spec/swagger.yaml",
            "/api/spec/swagger.yml",
            "/api/v1/swagger-ui/swagger.json",
            "/api/v1/swagger-ui/swagger.yaml",
            "/api/v1/swagger-ui/swagger.yml",
            "/api/swagger_doc.json",
            "/api/swagger_doc.yaml",
            "/api/swagger_doc.yml",
        ]
        return True

    async def handle_event(self, event):
        base_url = event.data.rstrip("/")
        for path in self.openapi_paths:
            apispec_url = self.helpers.urljoin(base_url, path)
            api_result = await self.helpers.request(apispec_url)
            status_code = getattr(api_result, "status_code", 0)
            if status_code == 200:
                self.log.info(f"GET {apispec_url} returned {status_code}")
                content_type = api_result.headers.get("Content-Type")
                if content_type == "application/json":
                    apispec = api_result.json()
                elif content_type == "text/yaml":
                    apispec = yaml.safe_load(api_result.text)
                await self.parse_openapi(base_url, apispec, event)

    async def parse_openapi(self, base_url, api_spec, source_event):
        servers = self.get_servers(api_spec.get("servers", []), base_url, api_spec=api_spec)
        parameters = {}
        for path_item in api_spec.get("apis", {}):
            path = path_item.get("path")
            operations = path_item.get("operations", [])
            for operation in operations:
                method = operation.get("method")
                parameters = await self.get_parameters(operation.get("parameters", []), api_spec)
                await self.send_request(method, list(set(servers)), path, parameters, source_event)
        for path in api_spec.get("paths", {}):
            path_items = api_spec["paths"][path]
            for path_item in path_items:
                if path_item == "parameters":
                    parameters.update(await self.get_parameters(path_items[path_item], api_spec))
                if path_item == "servers":
                    path_servers = self.get_servers(path_items[path_item], base_url)
                    servers = servers + path_servers
                elif path_item == "$ref":
                    path_item = await self.resolve_ref(path_items[path_item], api_spec)
                if path_item in ["get", "put", "post", "delete", "options", "head", "patch", "trace"]:
                    operation_parameters = await self.get_parameters(
                        path_items[path_item].get("parameters", []), api_spec
                    )
                    request_parameters = await self.get_requestBody(
                        path_items[path_item].get("requestBody", {}), api_spec, base_url
                    )
                    await self.send_request(
                        path_item.upper(),
                        list(set(servers)),
                        path,
                        {**parameters, **operation_parameters, **request_parameters},
                        source_event,
                    )

    async def send_request(self, method, servers, path, parameters, source_event):
        path_params = parameters.get("path", {})
        path = path.format(**path_params)
        for server in servers:
            url = server + path
            self.log.info(
                f"""{method} {url}
            Query: {parameters.get("query", {})}
            Headers: {parameters.get("header", {})}
            Cookies: {parameters.get("cookie", {})}
            Body: {parameters.get("body", {})}
            """
            )
            response = await self.helpers.request(
                method,
                url,
                params=parameters.get("query", {}),
                headers=parameters.get("header", {}),
                json=parameters.get("body", {}),
                cookies=parameters.get("cookie", {}),
            )
            status_code = getattr(response, "status_code", 0)
            self.log.info(response)
            if status_code == 200:
                tags = [f"status-{status_code}"]
                url_event = self.make_event(url, "URL", source_event, tags=tags)
                if url_event:
                    if url_event != source_event:
                        await self.emit_event(url_event)
                    else:
                        url_event._resolved.set()
                    await self.emit_event(response, "HTTP_RESPONSE", url_event, tags=url_event.tags)

    async def resolve_url(self, url):
        object = {}
        result = await self.helpers.request(url)
        status_code = getattr(result, "status_code", 0)
        self.log.info(f"GET {url} returned {status_code}")
        if status_code == 200:
            content_type = result.headers.get("Content-Type")
            if content_type == "application/json":
                object = result.json()
            elif content_type == "text/yaml":
                object = yaml.safe_load(result.text)
            else:
                object = result.text
        return object

    async def resolve_ref(self, ref, object, base_url=""):
        if "#/" in ref:
            location = ref.split("#/")[0]
            json_pointer = ref.split("#/")[1]
        else:
            location = ref
            json_pointer = ""
        if location:
            if not location.startswith("http"):
                location = self.helpers.urljoin(base_url, location)
            object = await self.resolve_url(location)
        if json_pointer:
            ref_parts = json_pointer.split("/")
            ref_data = object
            for part in ref_parts:
                ref_data = ref_data.get(part, {})
        else:
            ref_data = object
        return ref_data

    async def get_examples(self, examples, api_spec, base_url):
        """
        Get the examples from the OpenAPI specification
        {
          "foo": {
            "summary": "A foo example",
            "value": {"foo": "bar"}
            }
        }
        """
        for example_name, example_data in examples.items():
            if "value" in example_data:
                return example_data["value"]
            if "externalValue" in example_data:
                return await self.resolve_ref(example_data["externalValue"], api_spec, base_url=base_url)

    def get_servers(self, servers, base_url, api_spec={}):
        """
        Get the servers from the OpenAPI specification
        [{
          "url": "https://development.gigantic-server.com/v1",
          "description": "Development server"
        },
        {
          "url": "{protocol}://{host}",
          "description": "Development server",
          "variables": {"protocol": {"default": "https"}, "host": {"default": "localhost:3000"}
        }]
        """
        servers_list = []
        # For backwards compatability include the host and basePath
        host = api_spec.get("host")
        basePath = api_spec.get("basePath")
        schemes = api_spec.get("schemes", ["http"])
        if host:
            for scheme in schemes:
                if basePath:
                    servers_list.append(f"{scheme}://{host}{basePath}")
                else:
                    servers_list.append(f"{scheme}://{host}/")
        for server in servers:
            if "variables" in server:
                for variable, data in server["variables"].items():
                    if "default" in data:
                        server["url"] = server["url"].replace(f"{{{variable}}}", data["default"])
            servers_list.append(server["url"])
        if not servers_list:
            servers_list.append(base_url)
        return servers_list

    def rand_string(self, length):
        return self.helpers.rand_string(length, digits=False)

    def rand_int(self, length):
        return "".join([random.choice(string.digits) for _ in range(int(length))])

    async def get_schemas(self, schema, api_spec):
        """
        Get the schema from the OpenAPI specification
        {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "format": "int64"
            },
            "name": {
              "type": "string"
            }
          },
          "required": ["name"]
        }
        """
        schema_type = schema.get("type")
        if "$ref" in schema:
            schema = await self.resolve_ref(schema["$ref"], api_spec)
            schema_type = "object"
        schema_example = schema.get("example", "")
        if schema_example:
            return schema_example
        if schema_type == "object":
            properties = schema.get("properties", {})
            schema_dict = {}
            for property_name, property_data in properties.items():
                schema_dict[property_name] = await self.get_schemas(property_data, api_spec)
            return schema_dict
        elif schema_type == "array":
            items = schema.get("items", {})
            schema_list = await self.get_schemas(items, api_spec)
            return [schema_list]
        else:
            # format = schema.get("format", "")
            enums = schema.get("enum", [])
            if enums:
                return random.choice(enums)
            if schema_type == "string":
                return self.rand_string(6)
            elif schema_type == "integer" or schema_type == "number":
                return self.rand_int(6)

    async def get_parameters(self, parameters, api_spec):
        """
        Get the parameters from the OpenAPI specification
        [{
          "name": "token",
          "in": "header",
          "description": "token to be passed as a header",
          "required": true,
          "schema": {
            "type": "array",
            "items": {
              "type": "integer",
              "format": "int64"
            }
          },
          "style": "simple"
        },
        {
          "name": "username",
          "in": "path",
          "description": "username to fetch",
          "required": true,
          "schema": {
            "type": "string"
          }
        }]
        """
        if "$ref" in parameters:
            parameters = await self.resolve_ref(parameters["$ref"], api_spec)
        params = {}
        for parameter in parameters:
            location = parameter.get("in") or parameter.get("paramType")
            name = parameter.get("name")
            if "schema" not in parameter:
                schema = await self.get_schemas(parameter, api_spec)
            else:
                schema = await self.get_schemas(parameter.get("schema"), api_spec)
            param_dict = {name: schema}
            if name not in params:
                params[location] = param_dict
            else:
                params[location].update(param_dict)
        return params

    async def get_requestBody(self, requestBody, api_spec, base_url):
        """
        Get the body from the OpenAPI specification
        {
          "description": "user to add to the system",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/User"
              },
              "examples": {
                  "user" : {
                    "summary": "User Example",
                    "externalValue": "https://foo.bar/examples/user-example.json"
                  }
                }
            },
            "application/xml": {
              "schema": {
                "$ref": "#/components/schemas/User"
              },
              "examples": {
                  "user" : {
                    "summary": "User example in XML",
                    "externalValue": "https://foo.bar/examples/user-example.xml"
                  }
                }
            },
            "text/plain": {
              "examples": {
                "user" : {
                    "summary": "User example in Plain text",
                    "externalValue": "https://foo.bar/examples/user-example.txt"
                }
              }
            },
            "*/*": {
              "examples": {
                "user" : {
                    "summary": "User example in other format",
                    "externalValue": "https://foo.bar/examples/user-example.whatever"
                }
              }
            }
          }
        }
        """
        obj = {"body": {}}
        for content in requestBody.get("content", {}):
            schema = requestBody["content"][content].get("schema", {})
            if "$ref" in requestBody["content"][content]:
                schema = await self.resolve_ref(requestBody["content"][content]["$ref"], api_spec)
            obj["body"] = await self.get_schemas(schema, api_spec)
            if content == "application/xml":
                obj["body"] = dicttoxml2.dicttoxml(obj["body"], root=False)
            examples = requestBody["content"][content].get("examples", {})
            if examples:
                obj["body"] = await self.get_examples(examples, api_spec, base_url)
        return obj
