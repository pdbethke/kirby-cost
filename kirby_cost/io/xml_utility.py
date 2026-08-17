"""
XML Utility class for kirby-cost.

Converted from com.hero.util.XMLUtility.java

Provides utility methods for reading and writing XML elements.
Uses lxml ElementTree for XML manipulation (similar to JDOM in Java).
"""

from typing import Optional
from lxml import etree


class XMLUtility:
    """Utility class for XML operations."""
    
    @staticmethod
    def get_value(element: Optional[etree.Element], name: Optional[str]) -> str:
        """
        Get a value from an XML element.

        First tries to get the value as child text, then as an attribute.

        Args:
            element: The XML element to read from
            name: The name of the child element or attribute

        Returns:
            The value as a string, or empty string if not found
        """
        if name is None or element is None:
            return ""
        
        try:
            # Try to get as child element text
            child = element.find(name)
            if child is not None:
                text = child.text
                if text is not None and text.strip():
                    return text.strip()

            # Try to get as attribute
            attr_value = element.get(name)
            if attr_value is not None:
                return attr_value

            return ""
        except (etree.XPathEvalError, etree.LxmlError, AttributeError, TypeError) as e:
            # Log exception if logging is available
            # For now, just return empty string
            print(f"Error getting XML value '{name}': {e}")
            return ""
    
    @staticmethod
    def child_text(element: Optional[etree.Element], name: Optional[str]) -> str:
        """
        Get text from a child element.
        
        Args:
            element: The parent XML element
            name: The name of the child element
            
        Returns:
            The child element's text, or empty string if not found
        """
        if name is None or element is None:
            return ""
        
        try:
            child = element.find(name)
            if child is not None:
                text = child.text
                return text.strip() if text is not None else ""
            return ""
        except (etree.XPathEvalError, etree.LxmlError, AttributeError, TypeError) as e:
            print(f"Error getting child text '{name}': {e}")
            return ""
    
    @staticmethod
    def get_attribute(element: Optional[etree.Element], name: Optional[str]) -> str:
        """
        Get an attribute value from an XML element.
        
        Args:
            element: The XML element
            name: The attribute name
            
        Returns:
            The attribute value, or empty string if not found
        """
        if name is None or element is None:
            return ""
        
        try:
            attr_value = element.get(name)
            return attr_value if attr_value is not None else ""
        except (etree.LxmlError, AttributeError, TypeError) as e:
            print(f"Error getting attribute '{name}': {e}")
            return ""
    
    @staticmethod
    def set_value(element: etree.Element, name: str, value: str) -> None:
        """
        Set a value in an XML element.
        
        Creates a child element with the given name and text value.
        
        Args:
            element: The parent XML element
            name: The name of the child element to create
            value: The text value to set
        """
        if element is None or name is None:
            return
        
        try:
            # Remove existing child if it exists
            existing = element.find(name)
            if existing is not None:
                element.remove(existing)

            # Create new child element
            child = etree.SubElement(element, name)
            child.text = value if value is not None else ""
        except (etree.LxmlError, ValueError, TypeError) as e:
            print(f"Error setting XML value '{name}': {e}")
    
    @staticmethod
    def set_attribute(element: etree.Element, name: str, value: str) -> None:
        """
        Set an attribute value on an XML element.
        
        Args:
            element: The XML element
            name: The attribute name
            value: The attribute value
        """
        if element is None or name is None:
            return
        
        try:
            element.set(name, value if value is not None else "")
        except (etree.LxmlError, ValueError, TypeError) as e:
            print(f"Error setting attribute '{name}': {e}")
    
    @staticmethod
    def children(element: Optional[etree.Element], name: Optional[str] = None) -> list:
        """
        Get child elements from an XML element.
        
        Args:
            element: The parent XML element
            name: Optional name filter - if provided, only returns children with this name
            
        Returns:
            List of child elements
        """
        if element is None:
            return []
        
        try:
            if name is None:
                return list(element)
            else:
                return list(element.findall(name))
        except (etree.XPathEvalError, etree.LxmlError, AttributeError, TypeError) as e:
            print(f"Error getting children '{name}': {e}")
            return []
    
    @staticmethod
    def has_child(element: Optional[etree.Element], name: str) -> bool:
        """
        Check if an element has a child with the given name.
        
        Args:
            element: The parent XML element
            name: The child element name to check for
            
        Returns:
            True if the child exists, False otherwise
        """
        if element is None or name is None:
            return False
        
        try:
            return element.find(name) is not None
        except (etree.XPathEvalError, etree.LxmlError, AttributeError, TypeError):
            return False
    
    @staticmethod
    def has_attribute(element: Optional[etree.Element], name: str) -> bool:
        """
        Check if an element has an attribute with the given name.
        
        Args:
            element: The XML element
            name: The attribute name to check for
            
        Returns:
            True if the attribute exists, False otherwise
        """
        if element is None or name is None:
            return False
        
        try:
            return name in element.attrib
        except (etree.LxmlError, AttributeError, TypeError):
            return False



