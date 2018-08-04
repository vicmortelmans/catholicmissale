<?xml version="1.0"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="text" encoding="UTF-8"></xsl:output>
  <xsl:strip-space elements="*" />
  
  <xsl:param name="folder" select="'.'"/>

  <xsl:variable name="input" select="collection(concat($folder,'/?select=*.xml'))"/>

  <xsl:variable name="columns">
    <column>form</column>
    <column>coordinates</column>
    <column>name</column>
    <column>season</column>
    <column>set</column>
    <column>rank</column>
    <column>rankindex</column>
    <column>precedence</column>
    <column>vigil</column>
    <column>coincideswith</column>
    <column>color</column>
    <column>tide</column>
  </xsl:variable>
  
  <xsl:template match="/">
    <xsl:for-each select="$columns/column">
      <xsl:choose>
        <xsl:when test=". = 'form'">"<xsl:value-of select="."/>",</xsl:when>
        <xsl:when test="position() != last()">"<xsl:value-of select="."/>",</xsl:when>
        <xsl:when test="position() = last()">"<xsl:value-of select="."/>"</xsl:when>
      </xsl:choose>
    </xsl:for-each>
    <xsl:text>&#xA;</xsl:text>
    <xsl:apply-templates select="$input/*"/>
  </xsl:template>

  <xsl:template match="@*|node()">
    <xsl:apply-templates select="@*|node()"/>
  </xsl:template>
  
  <xsl:template match="liturgicalday">
    <xsl:variable name="liturgicalday" select="."/>
    <xsl:variable name="form" select="../form"/>
    <xsl:for-each select="$columns/column">
      <xsl:choose>
        <xsl:when test=". = 'form'">"<xsl:value-of select="$form"/>",</xsl:when>
        <xsl:when test=". = 'rankindex'">"<xsl:value-of select="$liturgicalday/rank/@nr"/>",</xsl:when>
        <xsl:when test="position() != last()">"<xsl:value-of select="$liturgicalday/*[name() = current()]"/>",</xsl:when>
        <xsl:when test="position() = last()">"<xsl:value-of select="$liturgicalday/*[name() = current()]"/>"</xsl:when>
      </xsl:choose>
    </xsl:for-each>
    <xsl:text>&#xA;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
