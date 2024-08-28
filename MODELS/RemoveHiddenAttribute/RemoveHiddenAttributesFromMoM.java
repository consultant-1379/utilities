import java.io.*;

import org.w3c.dom.*;
import org.xml.sax.*;

import javax.xml.parsers.*;
import javax.xml.transform.*; 
import javax.xml.transform.dom.DOMSource; 
import javax.xml.transform.stream.StreamResult;

public class RemoveHiddenAttributesFromMoM {
	
	static boolean enumAlreadyFound = false;
	
	static public void main(String[] arg) {
		try{
			//the first line argument must be the absolute path of the mp file
			if (arg.length != 0)
			{
			String xmlFile = arg[0]; 

			File file = new File(xmlFile);
			// name of the tag to remove
			String remElement = "filter"; //bf.readLine();
			String remElement2 = "extension"; 
			if (file.exists()){
				DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
				factory.setValidating(false);
				DocumentBuilder builder = factory.newDocumentBuilder();
				builder.setEntityResolver(new EntityResolver() {
			         
			         public InputSource resolveEntity(String publicId, String systemId)
	                 		throws SAXException, IOException {
				        	return new InputSource(new StringReader(""));
					}     
				});
				Document doc = builder.parse(xmlFile);
				TransformerFactory tFactory = TransformerFactory.newInstance();
				Transformer tFormer = tFactory.newTransformer();
    				tFormer.setOutputProperty(OutputKeys.DOCTYPE_SYSTEM, "mp.dtd");
					
				//remove all nodes in xml file with  remElement tag 
				removeAll(doc, Node.ELEMENT_NODE, remElement, remElement2);
				//Normalize the DOM tree to combine all adjacent nodes
				doc.normalize();
				Source source = new DOMSource(doc);
				Result dest = new StreamResult(System.out);
				tFormer.transform(source, dest);
				System.out.println();
			}
			else{
				System.out.println("File not found!");
			}
			}
			else{
				System.out.println("mp file name missing!");
			}
		}
		catch (Exception e){
			System.err.println(e);
			System.exit(0);
		}
	}
	
	// This method walks the document and removes all nodes
	// of the specified type and specified name.
	// If name is null, then the node is removed if the type matches.
	public static void removeAll(Node node, short nodeType, String name, String name2) {
		
		
		NamedNodeMap attrs = node.getAttributes();
		Node p;
		String attrName = null;
		if (attrs != null){
			p = attrs.getNamedItem("name");
			if (p != null)
			{
				attrName = p.getNodeValue();
				//System.out.println("attr name = "+attrName);
			}
		}
		
		//boolean isFilter = false;
		boolean isExtension = false;
	    if (node.getNodeType() == nodeType && (name == null || node.getNodeName().equals(name)))
	    {
	    	node.getParentNode().getParentNode().removeChild(node.getParentNode());
	    }
	    else
	    {
	    	if (node.getNodeType() == nodeType && 
	    		(name2 == null || ((node.getNodeName().equals(name2)))) && (attrName!=null && attrName.equals("filter")))
	    	{
	    		isExtension = true;
	    	
		    	String grandFather = node.getParentNode().getParentNode().getNodeName();
			    	
			    if ((isExtension) && (grandFather.equals("enum") || grandFather.equals("derivedDataType") || grandFather.equals("struct")))
			    {	
			    	node.getParentNode().getParentNode().getParentNode().removeChild(node.getParentNode().getParentNode());
			    }
	    	}
	    }
	       
        // Visit the children
        NodeList list = node.getChildNodes();
        for (int i=0; i<list.getLength(); i++) {
            removeAll(list.item(i), nodeType, name,name2);
        }

	}
}
