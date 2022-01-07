

Ili2db allows you to use three types of inheritance mapping:

- *noSmartMapping* This kind of inheritance maps all classes from the source INTERLIS model into the target database schema. Each class maintains all its attributes. Model Baker does not provide this option in the settings.
- *smart1inheritance* Form the inheritance hierarchy with a dynamic strategy. The NewClass strategy is used for classes that are referenced and whose base classes are not mapped using a NewClass strategy. Abstract classes are mapped using a SubClass strategy. Concrete classes, without a base class or their direct base classes with a SubClass strategy are mapped using a NewClass strategy. All other classes are mapped using a SuperClass strategy.
This kind of inheritance prefers to create parent classes into the database, as long as they fulfill some specific requirements. Attributes from children classes will not be lost, since they are transferred into parent ones.
- *smart2inheritance*: Abstract classes are mapped using a SubClass strategy. Concrete classes are mapped using a NewAndSubClass strategy.
This kind of inheritance prefers to create children classes into the database. Attribute from parent classes will not be lost, since they are transferred into children ones.
