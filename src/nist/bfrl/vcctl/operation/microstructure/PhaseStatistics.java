/*
 * PhaseStatistics.java
 *
 * Created on November 25, 2005, 3:54 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.operation.microstructure;

/**
 *
 * @author tahall
 */
public class PhaseStatistics {
    
    /** Creates a new instance of PhaseStatistics */
    public PhaseStatistics() {
    }
    
    public static String createHtml(String text) {
        
        StringBuffer htmlout = new StringBuffer("<b>Clinker Statistics:</b><br><br>");
        htmlout.append("<table>");
        String[] lines = text.split("\n");
        int iline = 0;
        for (iline=0; iline<2; iline++) {
            htmlout.append("<thead>");
            if (iline == 0) {
                htmlout.append("<th>Phase</th>");
            } else {
                htmlout.append("<th></th>");
            }
            String[] hdr = lines[iline].trim().split(" ");
            for (int i=0; i<hdr.length; i++) {
                String col = hdr[i].trim();
                if (col.length() > 0) {
                    htmlout.append("<th>"+col+"</th>");
                }
            }
            htmlout.append("</thead>");
        }
        while (!lines[iline].contains("Total")) {
            htmlout.append("<tr>");
            String[] hdr = lines[iline].trim().split(" ");
            for (int i=0; i<hdr.length; i++) {
                String col = hdr[i].trim();
                if (i == 0) {
                    int phaseno=0;
                    try {
                        phaseno = Integer.parseInt(col);
                    } catch (NumberFormatException ex) {
                        ex.printStackTrace();
                    }
                    String phname = Phase.name(phaseno);
                    htmlout.append("<td>"+phname+"</td>");
                }
                if (col.length() > 0) {
                    htmlout.append("<td>"+col+"</td>");
                }
            }
            htmlout.append("</tr>");
            iline++;
        }
        
        
        htmlout.append("</table>");
        
        return htmlout.toString();
    }
}
