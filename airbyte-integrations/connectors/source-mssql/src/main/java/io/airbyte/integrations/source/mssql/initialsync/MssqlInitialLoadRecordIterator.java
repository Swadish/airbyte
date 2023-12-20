package io.airbyte.integrations.source.mssql.initialsync;

import com.fasterxml.jackson.databind.JsonNode;
import com.google.common.collect.AbstractIterator;
import javax.annotation.CheckForNull;

public class MssqlInitialLoadRecordIterator extends AbstractIterator<JsonNode> {

  @CheckForNull
  @Override
  protected JsonNode computeNext() {
    return null;
  }
}
