# XSLT — это язык, который превращает XML в HTML, PDF или другой XML.

<xsl:template match="/">
   <html>
      <body>
         <h1><xsl:value-of select="user/name"/></h1>
         <p>Возраст: <xsl:value-of select="user/age"/></p>
      </body>
   </html>
</xsl:template>

# DTD — это правила, которые говорят: "В анкете должны быть имя, возраст и город, и ничего лишнего".

<!DOCTYPE user [
<!ELEMENT user (name, age, city)>
]>

# Entity (сущность) — это как шпаргалка, где написано: "Вместо &author; подставь 'Джон Доу'".

<!DOCTYPE note [
<!ENTITY author "Джон Доу">
]>
<note>
   <writer>&author;</writer>  <!-- Здесь подставится "Джон Доу" -->
</note>

