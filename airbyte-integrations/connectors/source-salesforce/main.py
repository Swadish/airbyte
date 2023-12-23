#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_salesforce import SourceSalesforce

if __name__ == "__main__":
    args = ['read', '--config', 'secrets/config.json', '--catalog', 'integration_tests/configured_catalog.json']
    source = SourceSalesforce()
    launch(source, args)
