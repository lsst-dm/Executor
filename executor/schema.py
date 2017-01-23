default = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "schema for Executor's job specification",
    "type": "object",
    "properties": {
        "task": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Task name"
                },
                "ids": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "List of task arguments"
                }
            },
            "required": [ "name", "args" ]
        },
        "input": { "$ref": "#/definitions/repository" },
        "output": { "$ref": "#/definitions/repository" },
        "calibs": {
            "type": "array",
            "items": { "$ref": "#/definitions/file" },
            "minItems": 1
        },
        "data": {
            "type": "array",
            "items": { "$ref": "#/definitions/file" },
            "minItems": 1
        }
    },
    "definitions": {
        "file": {
            "type": "object",
            "properties": {
                "pfn": {
                    "type": "string",
                    "description": "Physical file name"
                },
                "meta": {
                    "type": "object",
                    "description": "Metadata associated with the file"
                }
            },
            "required": [ "pfn", "meta" ]
        },
        "repository": {
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Location of the butler repository"
                },
                "mapper": {
                    "type": "string",
                    "description": "Butler repository mapper"
                }
            },
            "required": [ "root" ]
        }
    },
    "required": [ "task", "input", "output" ]
}
