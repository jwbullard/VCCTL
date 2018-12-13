/*
 * ServletChart.java
 *
 * Created on July 25, 2007, 12:20 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

/**
 *
 * @author mscialom
 */
public class ServletChart {
    
    /** Creates a new instance of ServletChart */
    
    public ServletChart(String map, String src, String useMap) {
        this.setMap(map);
        this.setSrc(src);
        this.setUseMap(useMap);
    }
    
    /**
     * Creates a new instance of ServletChart
     * Include useful values extracted from image map and chart axis ranges
     * Those values are used to allow the user to zoom on the image from the jsp page
     * See the javascript scripts associated with the measure-hydrated-mix.jsp page
     **/
    public ServletChart(String map, String src, String useMap,
            String xMin, String xMax, String yMin, String yMax,
            String xMinValue, String xMaxValue, String yMinValue, String yMaxValue) {
        this.setMap(map);
        this.setSrc(src);
        this.setUseMap(useMap);
        this.setXMin(xMin);
        this.setXMax(xMax);
        this.setYMin(yMin);
        this.setYMax(yMax);
        this.setXMinValue(xMinValue);
        this.setXMaxValue(xMaxValue);
        this.setYMinValue(yMinValue);
        this.setYMaxValue(yMaxValue);
    }
    
    /**
     * Holds value of property map.
     */
    private String map;
    
    /**
     * Getter for property map.
     * @return Value of property map.
     */
    public String getMap() {
        return this.map;
    }
    
    /**
     * Setter for property map.
     * @param map New value of property map.
     */
    public void setMap(String map) {
        this.map = map;
    }
    
    /**
     * Holds value of property src.
     */
    private String src;
    
    /**
     * Getter for property src.
     * @return Value of property src.
     */
    public String getSrc() {
        return this.src;
    }
    
    /**
     * Setter for property src.
     * @param src New value of property src.
     */
    public void setSrc(String src) {
        this.src = src;
    }
    
    /**
     * Holds value of property useMap.
     */
    private String useMap;
    
    /**
     * Getter for property useMap.
     * @return Value of property useMap.
     */
    public String getUseMap() {
        return this.useMap;
    }
    
    /**
     * Setter for property useMap.
     * @param useMap New value of property useMap.
     */
    public void setUseMap(String useMap) {
        this.useMap = useMap;
    }

    /**
     * Holds value of property xMin.
     */
    private String xMin;

    /**
     * Getter for property xMin.
     * @return Value of property xMin.
     */
    public String getXMin() {
        return this.xMin;
    }

    /**
     * Setter for property xMin.
     * @param xMin New value of property xMin.
     */
    public void setXMin(String xMin) {
        this.xMin = xMin;
    }

    /**
     * Holds value of property xMax.
     */
    private String xMax;

    /**
     * Getter for property xMax.
     * @return Value of property xMax.
     */
    public String getXMax() {
        return this.xMax;
    }

    /**
     * Setter for property xMax.
     * @param xMax New value of property xMax.
     */
    public void setXMax(String xMax) {
        this.xMax = xMax;
    }

    /**
     * Holds value of property yMin.
     */
    private String yMin;

    /**
     * Getter for property yMin.
     * @return Value of property yMin.
     */
    public String getYMin() {
        return this.yMin;
    }

    /**
     * Setter for property yMin.
     * @param yMin New value of property yMin.
     */
    public void setYMin(String yMin) {
        this.yMin = yMin;
    }

    /**
     * Holds value of property yMax.
     */
    private String yMax;

    /**
     * Getter for property yMax.
     * @return Value of property yMax.
     */
    public String getYMax() {
        return this.yMax;
    }

    /**
     * Setter for property yMax.
     * @param yMax New value of property yMax.
     */
    public void setYMax(String yMax) {
        this.yMax = yMax;
    }

    /**
     * Holds value of property xMaxValue.
     */
    private String xMaxValue;

    /**
     * Getter for property xMaxValue.
     * @return Value of property xMaxValue.
     */
    public String getXMaxValue() {
        return this.xMaxValue;
    }

    /**
     * Setter for property xMaxValue.
     * @param xMaxValue New value of property xMaxValue.
     */
    public void setXMaxValue(String xMaxValue) {
        this.xMaxValue = xMaxValue;
    }

    /**
     * Holds value of property xMinValue.
     */
    private String xMinValue;

    /**
     * Getter for property xMinValue.
     * @return Value of property xMinValue.
     */
    public String getXMinValue() {
        return this.xMinValue;
    }

    /**
     * Setter for property xMinValue.
     * @param xMinValue New value of property xMinValue.
     */
    public void setXMinValue(String xMinValue) {
        this.xMinValue = xMinValue;
    }

    /**
     * Holds value of property yMinValue.
     */
    private String yMinValue;

    /**
     * Getter for property yMinValue.
     * @return Value of property yMinValue.
     */
    public String getYMinValue() {
        return this.yMinValue;
    }

    /**
     * Setter for property yMinValue.
     * @param yMinValue New value of property yMinValue.
     */
    public void setYMinValue(String yMinValue) {
        this.yMinValue = yMinValue;
    }

    /**
     * Holds value of property yMaxValue.
     */
    private String yMaxValue;

    /**
     * Getter for property yMaxValue.
     * @return Value of property yMaxValue.
     */
    public String getYMaxValue() {
        return this.yMaxValue;
    }

    /**
     * Setter for property yMaxValue.
     * @param yMaxValue New value of property yMaxValue.
     */
    public void setYMaxValue(String yMaxValue) {
        this.yMaxValue = yMaxValue;
    }
    
}
