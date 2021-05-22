from conformity import fields

POST_SCHEMA = fields.Dictionary(
    {
        'cmd': fields.UnicodeString(
            description='Command that should be executed',
        ),
    },
)
