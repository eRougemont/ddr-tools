<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei">
  <xsl:import href="../../teinte-xsl/tei_common.xsl"/>
  <xsl:output encoding="UTF-8" method="text"/>

  <xsl:template match="/">
    <xsl:for-each select="//tei:div[@type = 'chapter']">
      
      <xsl:variable name="pages" select=".//tei:pb[@n]"/>
      <xsl:value-of select="@xml:id"/>
      <xsl:text>&#9;</xsl:text>
      <xsl:call-template name="title"/>
      <xsl:text>&#9;</xsl:text>
      <xsl:choose>
        <xsl:when test="not(tei:pb[not(preceding-sibling::tei:p)]) and .//tei:pb">
          <xsl:value-of select="preceding::tei:pb[@n][1]/@n"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$pages[1]/@n"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>&#9;</xsl:text>
      <xsl:value-of select="$pages[last()]/@n"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:transform>
