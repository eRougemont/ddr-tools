<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei">
  <xsl:import href="../../teinte-xsl/tei_common.xsl"/>
  <xsl:output encoding="UTF-8" method="html" omit-xml-declaration="yes"/>
  <xsl:variable name="published" select="substring(/*/@xml:id, 4, 4)"/>
  <xsl:variable name="booktitle">
    <xsl:choose>
      <xsl:when test="/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:monogr/tei:title">
        <xsl:apply-templates select="/tei:TEI/tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:monogr/tei:title"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy-of select="$doctitle"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="//tei:div[@type = 'chapter']">
        <xsl:apply-templates select="//tei:div[@type = 'chapter']"/>
      </xsl:when>
      <xsl:when test="//tei:div[@type = 'article']">
        <xsl:apply-templates select="//tei:div[@type = 'article']"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$filename"/>
        <xsl:text>&#10;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="tei:div[@type = 'chapter']">
    <li>
      <xsl:value-of select="substring($published, 1, 4)"/>
      <xsl:text> — </xsl:text>
      <i>
        <xsl:value-of select="normalize-space($booktitle)"/>
      </i>
      <xsl:text> — </xsl:text>
      <xsl:call-template name="title"/>
    </li>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>
  <xsl:template match="tei:div[@type = 'article']">
    <li>
      <xsl:value-of select="substring(@when, 1, 4)"/>
      <xsl:text> — </xsl:text>
      <xsl:choose>
        <xsl:when test="tei:head/tei:note[@type='bibl']//tei:ref">
          <xsl:apply-templates select="(tei:head/tei:note[@type='bibl']//tei:ref)[1]/node()"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="title"/>
        </xsl:otherwise>
      </xsl:choose>
    </li>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>
</xsl:transform>
