import json

QUESTIONS = {
    'body_condition': 'Rate the body condition from 1 to 10',
    'photo_quality': 'Rate the quality of the photos from 1 to 10',
    'car_cleanliness': 'Rate the cleanliness of the car from 1 to 10',
    'rust_presence': 'Are there any visible signs of rust? true/false',
    'glass_condition': 'Rate the condition of the windows from 1 to 10',
    'damage_severity': 'Rate the severity of visible damage from 1 to 10',
    'paint_condition': 'Rate the condition of the paintwork from 1 to 10',
    'wheel_condition': 'Rate the condition of the wheels and rims from 1 to 10',
}

RESPONSE_FORMAT = {
    'type': 'json_schema',
    'json_schema': {
        'name': 'car_visual_features',
        'schema': {
            'type': 'object',
            'properties': {
                'body_condition': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'photo_quality': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'car_cleanliness': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'rust_presence': {'type': 'boolean'},
                'glass_condition': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'damage_severity': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'paint_condition': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                'wheel_condition': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            },
            'required': [
                'body_condition',
                'photo_quality',
                'car_cleanliness',
                'rust_presence',
                'glass_condition',
                'damage_severity',
                'paint_condition',
                'wheel_condition',
            ],
            'additionalProperties': False,
        },
        'strict': True,
    },
}

PROMPT = f"""
Analyze the car photos and return ONLY valid JSON.

Extract the following features:
{json.dumps(QUESTIONS, indent=2)}

Example response format:
{{
  "body_condition": 8,
  "photo_quality": 9,
  "car_cleanliness": 8,
  "rust_presence": false,
  "glass_condition": 9,
  "damage_severity": 1,
  "paint_condition": 8,
  "wheel_condition": 7
}}

Do not explain anything.
Return ONLY valid JSON without markdown.
""".strip()
