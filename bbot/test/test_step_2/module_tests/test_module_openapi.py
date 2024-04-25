from .base import ModuleTestBase


class TestOpenAPI(ModuleTestBase):
    targets = ["http://127.0.0.1:8888"]
    modules_overrides = ["httpx", "openapi"]

    test_yaml = """---
openapi: ----
info:
  title: Test OpenAPI spec
  version: alpha
  description: Test OpenAPI spec, a mashup of OpenAPI 2.0 and 3.0 designed to test BBOT openapi module
paths:
  /pet:
    delete:
      parameters:
        - name: "petId"
          in: "query"
          type: "integer"
          example: 1
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Pet"
  /pet/{petId}:
    parameters:
    - name: "petId"
      in: "path"
      type: "integer"
      example: 1
    servers:
    - url: "http://127.0.0.1:8888/v2"
    get:
      parameters:
      - name: "Authorization"
        in: "header"
        type: "string"
        example: "test"
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Pet"
    put:
      requestBody:
        content:
          application/json:
            examples:
              user:
                externalValue: "https://example.com/v2/user/example.json"
components:
  schemas:
    Pet:
      type: "object"
      properties:
        name:
          type: "string"
        id:
          type: "integer"
        photoUrls:
          type: "array"
          items:
            type: "string"
        status:
          type: "string"
          enum:
            - "available"
            - "pending"
            - "sold"
servers:
- url: "{protocol}://{host}/v2"
  variables:
    protocol:
      default: http
    host:
      default: 127.0.0.1:8888
host: 127.0.0.1:8888
basePath: /v2
schemes: ["http"]
"""
    external_value_user_json = {"name": "username"}

    async def setup_after_prep(self, module_test):
        expect_args = {"method": "GET", "uri": "/swagger.yaml"}
        respond_args = {"headers": {"Content-Type": "text/yaml"}, "response_data": self.test_yaml}
        module_test.set_expect_requests(expect_args=expect_args, respond_args=respond_args)

        expect_args = {"method": "GET", "uri": "/v2/pet/1", "headers": {"Authorization": "test"}}
        respond_args = {"response_data": {"status": "ok"}}
        module_test.set_expect_requests(expect_args=expect_args, respond_args=respond_args)

        expect_args = {"method": "POST", "uri": "/v2/pet/1"}
        respond_args = {"response_data": "ok"}
        module_test.set_expect_requests(expect_args=expect_args, respond_args=respond_args)

        module_test.httpx_mock.add_response(
            url=f"https://example.com/v2/user/example.json",
            json=self.external_value_user_json,
        )

        expect_args = {
            "method": "PUT",
            "uri": "/v2/pet/1",
            "data": {"name": "username"},
        }
        respond_args = {"response_data": "ok"}
        module_test.set_expect_requests(expect_args=expect_args, respond_args=respond_args)

        expect_args = {"method": "DELETE", "uri": "/v2/pet/1", "query_string": {"petId": 1}}
        respond_args = {"response_data": "ok"}
        module_test.set_expect_requests(expect_args=expect_args, respond_args=respond_args)

    def check(self, module_test, events):
        assert 2 == len([e for e in events if e.type == "URL" and "http://127.0.0.1:8888/v2/pet/" in e.data]), [
            e.data for e in events if e.type == "URL"
        ]
        assert 2 == len(
            [e for e in events if e.type == "HTTP_RESPONSE" and "ok" in e.data]
        ), "Failed to raise all HTTP_RESPONSE's from the openapi spec"
