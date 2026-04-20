"""Federation Adapter Layer.

Abstracts the difference between ECP's native stores and external context
sources. The Resolution Engine queries adapters in parallel; results are
merged with source attribution; conflicts are resolved by certification
tier, precedence, or disambiguation prompt.

"""
