/*
 * HydrationResults.java
 *
 * Created on July 22, 2007, 6:06 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

import java.util.*;
import nist.bfrl.vcctl.util.Util;
import org.jfree.chart.JFreeChart;

/**
 *
 * @author mscialom
 */
public class HydrationResults {
    
    /** Creates a new instance of HydrationResults */
    public HydrationResults(String userName, String hydrationName) {
        this.setUserName(userName);
        this.setHydrationName(hydrationName);
        hydrationResultsArray = HydratedMixMeasurements.getResults(userName, hydrationName, "data");
        if (hydrationResultsArray != null) {
         // purgedHydrationResultsArray = HydratedMixMeasurements.purgeResults(hydrationResultsArray);
            purgedHydrationResultsArray = hydrationResultsArray;
            this.setXAxisName(purgedHydrationResultsArray[1][0]);
        }
    }
    
    /**
     * Holds value of property hydrationResultsArray.
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     */
    private String[][] hydrationResultsArray;

    /**
     * Getter for property hydrationResultsArray.
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     * @return Value of property hydrationResultsArray.
     */
    public String[][] getHydrationResultsArray() {
        return this.hydrationResultsArray;
    }

    /**
     * Setter for property hydrationResultsArray.
     * @param hydrationResultsArray New value of property hydrationResultsArray.
     */
    public void setHydrationResultsArray(String[][] hydrationResultsArray) {
        this.hydrationResultsArray = hydrationResultsArray;
    }

    /**
     * Holds value of property purgedHydrationResultsArray.
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     */
    private String[][] purgedHydrationResultsArray;

    /**
     * Getter for property purgedHydrationResultsArray.
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     * @return Value of property purgedHydrationResultsArray.
     */
    public String[][] getPurgedHydrationResultsArray() {
        return this.purgedHydrationResultsArray;
    }

    /**
     * Setter for property purgedHydrationResultsArray.
     * @param purgedHydrationResultsArray New value of property purgedHydrationResultsArray.
     */
    public void setPurgedHydrationResultsArray(String[][] purgedHydrationResultsArray) {
        this.purgedHydrationResultsArray = purgedHydrationResultsArray;
    }

    private String hydrationName;

    /**
     * Getter for property hydrationName.
     * @return Value of property hydrationName.
     */
    public String getHydrationName() {
        return this.hydrationName;
    }

    /**
     * Setter for property hydrationName.
     * @param hydrationName New value of property hydrationName.
     */
    public void setHydrationName(String hydrationName) {
        this.hydrationName = hydrationName;
    }

    /**
     * Holds value of property xAxisName.
     */
    private String xAxisName;

    /**
     * Getter for property xAxisName.
     * @return Value of property xAxisName.
     */
    public String getXAxisName() {
        return this.xAxisName;
    }

    /**
     * Setter for property xAxisName.
     * @param xAxisName New value of property xAxisName.
     */
    public void setXAxisName(String xAxisName) {
        this.xAxisName = xAxisName;
    }

    /**
     * Holds value of property xAxisDisplayName.
     */
    private String xAxisDisplayName;

    /**
     * Getter for property xAxisDisplayName.
     * @return Value of property xAxisDisplayName.
     */
    public String getXAxisDisplayName() {
        return this.xAxisDisplayName;
    }

    /**
     * Setter for property xAxisDisplayName.
     * @param xAxisDisplayName New value of property xAxisDisplayName.
     */
    public void setXAxisDisplayName(String xAxisDisplayName) {
        this.xAxisDisplayName = xAxisDisplayName;
    }

    /**
     * Holds value of property yPlottingElementsHydrationProperties.
     */
    private List<String> yPlottingElementsNames;

    /**
     * Getter for property yPlottingElementsNames.
     * @return Value of property yPlottingElementsNames.
     */
    public List<String> getYPlottingElementsNames() {
        return this.yPlottingElementsNames;
    }

    /**
     * Setter for property yPlottingElementsNames.
     * @param yPlottingElementsNames New value of property yPlottingElementsNames.
     */
    public void setYPlottingElementsNames(List<String> yPlottingElementsNames) {
        this.yPlottingElementsNames = yPlottingElementsNames;
    }

    /**
     * Holds value of property yPlottingElementsDisplayNames.
     */
    private List<String> yPlottingElementsDisplayNames;

    /**
     * Getter for property yPlottingElementsDisplayNames.
     * @return Value of property yPlottingElementsDisplayNames.
     */
    public List<String> getYPlottingElementsDisplayNames() {
        return this.yPlottingElementsDisplayNames;
    }

    /**
     * Setter for property yPlottingElementsDisplayNames.
     * @param yPlottingElementsDisplayNames New value of property yPlottingElementsDisplayNames.
     */
    public void setYPlottingElementsDisplayNames(List<String> yPlottingElementsDisplayNames) {
        this.yPlottingElementsDisplayNames = yPlottingElementsDisplayNames;
    }
    
    public Collection getXLabels() {
        ArrayList<String> l = new ArrayList();
        String name, displayName;
        String[] elementsNames = new String[yPlottingElementsNames.size()];
        yPlottingElementsNames.toArray(elementsNames);
        for (int i = 0; i < purgedHydrationResultsArray.length; i++) {
            name = purgedHydrationResultsArray[i][0];
            displayName = DataTypes.displayNameOf(name);
            if (Util.searchStringInArray(name, elementsNames) < 0) {
                l.add(displayName);
            }
        }
        return l;
    }
    
    public ArrayList<String> getYLabels() {
        ArrayList<String> l = new ArrayList();
        String name, displayName;
        for (int i = 0; i < purgedHydrationResultsArray.length; i++) {
            name = purgedHydrationResultsArray[i][0];
            displayName = DataTypes.displayNameOf(name);
            if (!name.equalsIgnoreCase(xAxisName)) {
                l.add(displayName);
            }
        }
        return l;
    }
    
    public String[] xValues(String columnName) {
        for (int i = 0; i < purgedHydrationResultsArray.length; i++) {
            if (purgedHydrationResultsArray[i][0].equalsIgnoreCase(columnName)) {
                int valuesNumber = purgedHydrationResultsArray[i].length - 1;
                String[] xValues = new String[valuesNumber-1];
                for (int j = 0; j < valuesNumber - 1; j++) {
                    xValues[j] = purgedHydrationResultsArray[i][j+1];
                }
                return xValues;
            }
        }
        return null;
}

    public String[] yValues(String columnName) {
        int linesNumber = purgedHydrationResultsArray[0].length - 1;
        String[] yValues = new String[linesNumber-1];
        for (int i = 0; i < purgedHydrationResultsArray.length; i++) {
            if (purgedHydrationResultsArray[i][0].equalsIgnoreCase(columnName)) {
                int valuesNumber = purgedHydrationResultsArray[i].length - 1;
                for (int j = 0; j < valuesNumber - 1; j++) {
                    yValues[j] = purgedHydrationResultsArray[i][j+1];
                }
            }
        }
        if (yValues[0] != null)
            return yValues;
        return null;
    }

   // public JFreeChart generateGraph() {
   //     return generateGraph(0.0,0.0);
   // }
    
   // public JFreeChart generateGraph(double xMin, double xMax) {
   //     String xUnit = DataTypes.unitOf(xAxisName);
   //     String yUnit = DataTypes.unitOf(yPlottingElementsNames.get(0));
   //     String[] propertyDisplayNames = new String[yPlottingElementsNames.size()];
   //     yPlottingElementsNames.toArray(propertyDisplayNames);
   //     String[] names = new String[yPlottingElementsNames.size()];
   //     yPlottingElementsNames.toArray(names);
   //     return HydratedMixMeasurements.generateGraph(hydrationName,
   //             xAxisDisplayName,
   //             propertyDisplayNames,
   //             xUnit,
   //             yUnit,
   //             xValues(xAxisName),
   //             yValues(names),
   //             xMin,
   //             xMax);
   // }

    /**
     * Holds value of property userName.
     */
    private String userName;

    /**
     * Getter for property userName.
     * @return Value of property userName.
     */
    public String getUserName() {
        return this.userName;
    }

    /**
     * Setter for property userName.
     * @param userName New value of property userName.
     */
    public void setUserName(String userName) {
        this.userName = userName;
    }
}
