<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.tei-c.org/ns/1.0"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  exclude-result-prefixes="tei"

  >
  <xsl:output encoding="UTF-8" method="xml" indent="yes" cdata-section-elements="xenoData"/>
  <xsl:param name="filename"/>
  <xsl:param name="id">
    <xsl:value-of select="/*/@xml:id"/>
  </xsl:param>
  <xsl:param name="cert"/>
  <xsl:param name="type">
    <xsl:choose>
      <xsl:when test=".//tei:div[@type = 'chapter']">book</xsl:when>
      <xsl:otherwise>article</xsl:otherwise>
    </xsl:choose>
  </xsl:param>
  <xsl:variable name="lf" select="'&#10;'"/>
  <xsl:template match="node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/processing-instruction()" priority="1">
    <xsl:copy/>
    <xsl:value-of select="$lf"/>
  </xsl:template>
  <xsl:template match="/*">
    <xsl:variable name="idfile" select="substring-before(concat($filename, '_'), '_')"/>
    <xsl:choose>
      <xsl:when test="$idfile != $id">
        <xsl:message>
          <xsl:value-of select="$idfile"/>
          <xsl:text>!=</xsl:text>
          <xsl:value-of select="$id"/>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:attribute name="xml:id">
        <xsl:value-of select="$id"/>
      </xsl:attribute>
      <xsl:if test="$cert != ''">
        <xsl:attribute name="cert">
          <xsl:value-of select="$cert"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="type">
        <xsl:value-of select="$type"/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="tei:div[@type = 'chapter']">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:attribute name="xml:id">
        <xsl:value-of select="$id"/>
        <xsl:text>_</xsl:text>
        <xsl:number count="tei:div[@type = 'chapter']" format="01" level="any"/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
</xsl:transform>