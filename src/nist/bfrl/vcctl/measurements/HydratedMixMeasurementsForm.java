/*
 * HydratedMixMeasurementsForm.java
 *
 * Created on July 20, 2007, 10:25 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.measurements;

import java.io.File;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.SortedMap;
import java.util.ArrayList;
import nist.bfrl.vcctl.database.CementDatabase;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.NoHydrationResultsException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.operation.microstructure.GenerateMicrostructureForm;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;
import org.apache.struts.action.ActionForm;
import org.jfree.chart.JFreeChart;

/**
 *
 * @author mscialom
 */
public class HydratedMixMeasurementsForm extends ActionForm {

    public void init(String userName, String hydrationName, HydrationResults hydrationResults) throws NoHydrationResultsException, SQLArgumentException, SQLException {
        if (hydrationName.length() != 0) {
            // String[][] purgedHydrationResults = hydrationResults.getPurgedHydrationResultsArray();
            String[][] purgedHydrationResults = hydrationResults.getHydrationResultsArray();
            if (purgedHydrationResults != null && purgedHydrationResults.length > 1) {

                String name = purgedHydrationResults[1][0];
                this.setXAxis(DataTypes.displayNameOf(name));
                hydrationResults.setXAxisName(name);
                hydrationResults.setXAxisDisplayName(xAxis);

                ArrayList<String> names = new ArrayList();
                names.add(purgedHydrationResults[2][0]);
                ArrayList<YPlottingElement> displayElements = new ArrayList();
                displayElements.add(new YPlottingElement(hydrationName,DataTypes.displayNameOf(purgedHydrationResults[2][0]),hydrationResults));
                this.setYPlottingElements(displayElements);

                ArrayList<String> displayElements2 = new ArrayList();
                displayElements2.add(displayElements.get(0).getHydrationProperty());

                hydrationResults.setYPlottingElementsNames(names);
                hydrationResults.setYPlottingElementsDisplayNames(displayElements2);
                 yPlottingElements.get(0).setHydrationResults(hydrationResults);
                ArrayList<String> al = yPlottingElements.get(0).getYLabels();

                this.setYLabels(al);
               
                this.setChartXMax("0.0");
                this.setChartXMin("0.0");
            } else {
                throw new NoHydrationResultsException("There are no results for this hydrated mix");
            }
        }
    }

    /**
     * Creates a new instance of HydratedMixMeasurementsForm
     */
    public HydratedMixMeasurementsForm() {
    }

    public void updateHydrationResults() {
        HydrationResults hydrationResults;
        String displayProperty,hydrationName;
        for (int i = 0; i < yPlottingElements.size(); i++) {
            hydrationResults = yPlottingElements.get(i).getHydrationResults();
            hydrationName = yPlottingElements.get(i).getHydrationName();
            displayProperty = yPlottingElements.get(i).getHydrationProperty();
            hydrationResults.setHydrationName(hydrationName);
            hydrationResults.setXAxisDisplayName(xAxis);
            hydrationResults.setXAxisName(DataTypes.nameOf(xAxis));
            ArrayList<String> displayProperties = new ArrayList();
            ArrayList<String> properties = new ArrayList();
            displayProperties.add(displayProperty);
            properties.add(DataTypes.nameOf(displayProperty));
            hydrationResults.setYPlottingElementsDisplayNames(displayProperties);
            hydrationResults.setYPlottingElementsNames(properties);
            yPlottingElements.get(i).setHydrationResults(hydrationResults);
        }
        
        
    }

    public void replaceHydrationResults(String userName) {
        String displayProperty,hydrationName;
        for (int i = 0; i < yPlottingElements.size(); i++) {
            hydrationName = yPlottingElements.get(i).getHydrationName();
            HydrationResults hydrationResults = new HydrationResults(userName,hydrationName);
            displayProperty = yPlottingElements.get(i).getHydrationProperty();
            hydrationResults.setHydrationName(hydrationName);
            hydrationResults.setXAxisDisplayName(xAxis);
            hydrationResults.setXAxisName(DataTypes.nameOf(xAxis));
            ArrayList<String> displayProperties = new ArrayList();
            ArrayList<String> properties = new ArrayList();
            displayProperties.add(displayProperty);
            properties.add(DataTypes.nameOf(displayProperty));
            hydrationResults.setYPlottingElementsDisplayNames(displayProperties);
            hydrationResults.setYPlottingElementsNames(properties);
            yPlottingElements.get(i).setHydrationResults(hydrationResults);
        }
    }

    /**
     * Holds value of property xAxis.
     */
    private String xAxis;

    /**
     * Getter for property xAxis.
     * @return Value of property xAxis.
     */
    public String getXAxis() {
        return this.xAxis;
    }

    /**
     * Setter for property xAxis.
     * @param xAxis New value of property xAxis.
     */
    public void setXAxis(String xAxis) {
        this.xAxis = xAxis;
    }

    /**
     * Getter for property xLabels.
     * @return Value of property xLabels.
     */
    public Collection getXLabels() {
        return yPlottingElements.get(0).getHydrationResults().getXLabels();
    }
    /**
     * Holds value of property yPlottingElements.
     */
    private List<YPlottingElement> yPlottingElements;

    /**
     * Getter for property yPlottingElements.
     * @return Value of property yPlottingElements.
     */
    public List<YPlottingElement> getYPlottingElements() {
        return this.yPlottingElements;
    }

    /**
     * Setter for property yPlottingElements.
     * @param yPlottingElements New value of property yPlottingElements.
     */
    public void setYPlottingElements(List<YPlottingElement> yPlottingElements) {
        this.yPlottingElements = yPlottingElements;
    }

    /**
     * Remove from the list all the y labels that don't have the same unit as the first selected one
     **/
    public void removeIncompatibleLabels() {
        for (int i = 0; i < yPlottingElements.size(); i++) {
            this.setYLabels(yPlottingElements.get(i).getHydrationResults().getYLabels());
            String unit = DataTypes.unitOfDisplayName(yPlottingElements.get(0).getHydrationProperty());
            ArrayList<String> iLabel = this.getYLabels();
            String label;
            for (int j = 0; j < iLabel.size(); j++) {
                label = iLabel.get(j);
                if (!DataTypes.unitOfDisplayName(label).equalsIgnoreCase(unit) || label.equalsIgnoreCase(xAxis)) {
                    iLabel.remove(j);
                    j--;
                }
            }
            this.setYLabels(iLabel);
        }
    }

    /**
     * Remove from list if it's already the x axis
     * Add the first element that is not already plotted
     **/
    public void addYPlottingElement() {
        ArrayList<String> backupLabels = this.getYLabels();
        removeIncompatibleLabels();
        boolean elementAdded = false;
        boolean alreadyUsed;
        String name,usedProperty;
        String property = "";
        String hydrationName = yPlottingElements.get(yPlottingElements.size()-1).getHydrationName();
        String userName = yPlottingElements.get(yPlottingElements.size()-1).getHydrationResults().getUserName();
        for (int i = 0; i < this.yLabels.size(); i++) {
            alreadyUsed = false;
            property = this.yLabels.get(i);
            if (this.yLabels.size() > 1) {
                for (int j = 0; j < yPlottingElements.size(); j++) {
                    name = yPlottingElements.get(j).getHydrationName();
                    if (name.equalsIgnoreCase(hydrationName)) {
                        usedProperty = yPlottingElements.get(j).getHydrationProperty();
                        if (property.equalsIgnoreCase(usedProperty)) {
                            alreadyUsed = true;
                            break;
                        }
                    }
                }
            }
            // if (!alreadyUsed) {
                HydrationResults hydrationResults = new HydrationResults(userName,hydrationName);
                addYPlottingElement(new YPlottingElement(hydrationName,property,hydrationResults));
                elementAdded = true;
                break;
            // }
        }
        // if no element has been added, go back to the original set of labels
        if (!elementAdded) {
            this.setYLabels(backupLabels);
        }
    }

    public void addYPlottingElement(YPlottingElement yPlottingElement) {
        yPlottingElements.add(yPlottingElement);
    }

    public void removeYPlottingElement(int i) {
        yPlottingElements.remove(i);
        if (yPlottingElements.size() == 1) {
            this.setYLabels(yPlottingElements.get(0).getHydrationResults().getYLabels());
        }
    }
    
    /**
     * Holds value of property userFinishedHydratedMixList.
     */
    private Collection<String> userFinishedHydratedMixList;

    /**
     * Getter for property userFinishedHydratedMixList.
     * @return Value of property userFinishedHydratedMixList.
     */
    public Collection<String> getUserFinishedHydratedMixList() {
        return this.userFinishedHydratedMixList;
    }

    /**
     * Setter for property userFinishedHydratedMixList.
     * @param userHydratedMixList New value of property userFinishedHydratedMixList.
     */
    public void setUserFinishedHydratedMixList(Collection<String> userFinishedHydratedMixList) {
        this.userFinishedHydratedMixList = userFinishedHydratedMixList;
    }
    /**
     * Holds value of property xUnit.
     */
    private String xUnit;
    /**
     * Holds value of property yUnit.
     */
    private String yUnit;

    /**
     * Getter for property yPlottingElement.
     * @return Value of property yPlottingElement.
     */
    public YPlottingElement getYPlottingElement(int index) {
        return (YPlottingElement) yPlottingElements.get(index);
    }

    public JFreeChart generateGraph() {
        updateHydrationResults();
        String xAxisDisplayName = getXAxisDisplayName();
        String xUnit = DataTypes.unitOf(getXAxisName());
        String yName = yPlottingElements.get(0).getHydrationProperty();
        String yUnit = DataTypes.unitOfDisplayName(yName);
        ArrayList<String> propertyDisplayNames = new ArrayList();
        ArrayList<String> names = new ArrayList();
        ArrayList<Curve> curves = new ArrayList();
        for (int i = 0; i < yPlottingElements.size(); i++) {
            curves.add(yPlottingElements.get(i).getCurve());
            propertyDisplayNames.add(yPlottingElements.get(i).getHydrationPropertyDisplayName());
            names.add(yPlottingElements.get(i).getYPlottingElementsNames());
        }
       
        if (chartXMin != null && chartXMax != null) {
            double xMin = Double.parseDouble(chartXMin);
            double xMax = Double.parseDouble(chartXMax);
            if (xMin < xMax) {
                return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves,xMin,xMax);
            } else {
                return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves);
            }
        } else {
            return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves);
        }
    }

    public JFreeChart generateGraph(double xMin, double xMax) {
        updateHydrationResults();
        String xAxisDisplayName = getXAxisDisplayName();
        String xUnit = DataTypes.unitOf(getXAxisName());
        String yName = yPlottingElements.get(0).getHydrationProperty();
        String yUnit = DataTypes.unitOfDisplayName(yName);
        ArrayList<String> propertyDisplayNames = new ArrayList();
        ArrayList<String> names = new ArrayList();
        ArrayList<Curve> curves = new ArrayList();
        for (int i = 0; i < yPlottingElements.size(); i++) {
            curves.add(yPlottingElements.get(i).getCurve());
            propertyDisplayNames.add(yPlottingElements.get(i).getHydrationPropertyDisplayName());
            names.add(yPlottingElements.get(i).getYPlottingElementsNames());
        }
        return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves,xMin,xMax);
    }

        public JFreeChart generateGraphFromNewMix(String userName) {
        // If we have a new mix, then we have to make a new HydrationResult and
        // replace it.  We don't know which one, so we do it to all of them
        replaceHydrationResults(userName);
        String xAxisDisplayName = getXAxisDisplayName();
        String xUnit = DataTypes.unitOf(getXAxisName());
        String yName = yPlottingElements.get(0).getHydrationProperty();
        String yUnit = DataTypes.unitOfDisplayName(yName);
        ArrayList<String> propertyDisplayNames = new ArrayList();
        ArrayList<String> names = new ArrayList();
        ArrayList<Curve> curves = new ArrayList();
        for (int i = 0; i < yPlottingElements.size(); i++) {
            curves.add(yPlottingElements.get(i).getCurve());
            propertyDisplayNames.add(yPlottingElements.get(i).getHydrationPropertyDisplayName());
            names.add(yPlottingElements.get(i).getYPlottingElementsNames());
        }

        if (chartXMin != null && chartXMax != null) {
            double xMin = Double.parseDouble(chartXMin);
            double xMax = Double.parseDouble(chartXMax);
            if (xMin < xMax) {
                return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves,xMin,xMax);
            } else {
                return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves);
            }
        } else {
            return HydratedMixMeasurements.generateGraph(xAxisDisplayName,propertyDisplayNames,xUnit,yUnit,curves);
        }
    }

    public class YPlottingElement {

        /**
         * Holds value of property hydrationName.
         */
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
         * Holds value of property hydrationProperty.
         */
        private String hydrationProperty;

        /**
         * Getter for property hydrationProperty.
         * @return Value of property hydrationProperty.
         */
        public String getHydrationProperty() {
            return this.hydrationProperty;
        }

        /**
         * Setter for property hydrationProperty.
         * @param hydrationProperty New value of property hydrationProperty.
         */
        public void setHydrationProperty(String hydrationProperty) {
            this.hydrationProperty = hydrationProperty;
        }

        /**
         * Holds value of property hydrationResults.
         */
        private HydrationResults hydrationResults;

        /**
         * Getter for property hydrationResults.
         * @return Value of property hydrationResults.
         */
        public HydrationResults getHydrationResults() {
            return this.hydrationResults;
        }

        /**
         * Setter for property hydrationResults.
         * @param hydrationResults New value of property hydrationResults.
         */
        public void setHydrationResults(HydrationResults hydrationResults) {
            this.hydrationResults = hydrationResults;
        }

        /**
         * Getter for xAxisDisplayName.
         * @return Value of property xAxisDisplayName.
         */
        public String getXAxisDisplayName() {
            return hydrationResults.getXAxisDisplayName();
        }
        
        /**
         * Getter for hydrationPropertyDisplayName.
         * @return Value of property hydrationPropertyDisplayName.
         */
        public String getHydrationPropertyDisplayName() {
            return hydrationResults.getYPlottingElementsDisplayNames().get(0);
        }
        
        /**
         * Getter for yPlottingElementsNames.
         * @return Value of property yPlottingelementsNames.
         */
        public String getYPlottingElementsNames() {
            return hydrationResults.getYPlottingElementsNames().get(0);
        }

        /**
         * Getter for yPlottingElementsNames.
         * @return Value of property yPlottingelementsNames.
         */
        public ArrayList<String> getYLabels() {
            return hydrationResults.getYLabels();
        }

        /**
         * Getter for xAxisName.
         * @return Value of property xAxisDisplayName.
         */
        public String getXAxisName() {
            return hydrationResults.getXAxisName();
        }
        
        /**
         * Processes the yPlottingElement into Curve data and returns the curve
         * @return Value of curve
         */
        public Curve getCurve() {
          String[] xValues = hydrationResults.xValues(getXAxisName());
          String propertyName = hydrationResults.getYPlottingElementsNames().get(0);
          String[] yValues = hydrationResults.yValues(propertyName);
          Curve curve = new Curve(xValues,yValues,this.hydrationName,this.hydrationProperty);
          return curve;
            
        }
        
        public YPlottingElement(String hydrationName, String hydrationProperty, HydrationResults hydrationResults) {
            this.hydrationName = hydrationName;
            this.hydrationProperty = hydrationProperty;
            this.hydrationResults = hydrationResults;
        }

        public YPlottingElement(String hydrationName, String hydrationProperty) {
            this.hydrationName = hydrationName;
            this.hydrationProperty = hydrationProperty;
        }

        public YPlottingElement() { }

    }
    
    /**
     * Getter for property xAxisDisplayName.
     * @return Value of property xAxisDisplayName.
     */
    public String getXAxisDisplayName() {
        return yPlottingElements.get(0).getXAxisDisplayName();
    }
    
    /**
     * Getter for property xAxisName.
     * @return Value of property xAxisName.
     */
    public String getXAxisName() {
        return yPlottingElements.get(0).getXAxisName();
    }
    
    /**
     * Holds value of property yLabels.
     */
    private ArrayList<String> yLabels;

    /**
     * Getter for property yLabels.
     * @return Value of property yLabels.
     */
    public ArrayList<String> getYLabels() {
        return this.yLabels;
    }

    /**
     * Setter for property yLabels.
     * @param yLabels New value of property yLabels.
     */
    public void setYLabels(ArrayList<String> yLabels) {
        this.yLabels = yLabels;
    }
    
    /**
     * Holds value of property chartXMin.
     */
    private String chartXMin;

    /**
     * Getter for property chartXMin.
     * @return Value of property chartXMin.
     */
    public String getChartXMin() {
        return this.chartXMin;
    }

    /**
     * Setter for property chartXMin.
     * @param chartXMin New value of property chartXMin.
     */
    public void setChartXMin(String chartXMin) {
        this.chartXMin = chartXMin;
    }
    /**
     * Holds value of property chartXMax.
     */
    private String chartXMax;

    /**
     * Getter for property chartXMax.
     * @return Value of property chartXMax.
     */
    public String getChartXMax() {
        return this.chartXMax;
    }

    /**
     * Setter for property chartXMax.
     * @param chartXMax New value of property chartXMax.
     */
    public void setChartXMax(String chartXMax) {
        this.chartXMax = chartXMax;
    }
}
