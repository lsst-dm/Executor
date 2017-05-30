default = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "schema for Executor's job specification",
    "type": "object",
    "properties": {
        "task": { "$ref": "#/definitions/task" },
        "input": { "$ref": "#/definitions/input" },
        "output": { "$ref": "#/definitions/output" },
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
        "task": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Task name"
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of task arguments"
                }
            },
            "required": [ "name", "args" ]
        },
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
        "input": {
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Location of the dataset repository"
                },
                "mapper": {
                    "type": "string",
                    "description": "Dataset repository mapper"
                },
                "readonly": {
                    "type": "boolean",
                    "default": True,
                }
            },
            "required": [ "root", "mapper" ]
        },
        "output": {
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Location of the dataset repository"
                },
                "mapper": {
                    "type": "string",
                    "description": "Dataset repository mapper"
                }
            },
            "required": [ "root" ]
        }
    },
    "required": [ "task", "input", "output" ]
}
