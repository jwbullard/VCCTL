/*
 * HydratedMixMeasurements.java
 *
 * Created on July 19, 2007, 12:19 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

import java.awt.Color;
import java.awt.Font;
import java.awt.BasicStroke;
import java.awt.Dimension;
import java.io.*;
import java.util.ArrayList;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.application.Vcctl;
import org.jfree.chart.*;
import org.jfree.chart.plot.*;
import org.jfree.data.*;
import org.jfree.data.xy.*;
import org.jfree.chart.renderer.xy.XYItemRenderer;
import org.jfree.chart.renderer.category.CategoryItemRenderer;
import org.jfree.data.category.DefaultCategoryDataset;
import org.jfree.ui.ApplicationFrame;
import org.jfree.ui.RefineryUtilities;

/**
 *
 * @author mscialom
 */
public class HydratedMixMeasurements {
    
    /**
     * Get the results by parsing the .extension file
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     **/
    static public String[][] getResults(String userName, String operationName, String extension) {
        if (!extension.startsWith("."))
            extension = "." + extension;
        String results = ServerFile.readTextFile(ServerFile.getUserOperationDir(userName, operationName),operationName + extension);
        String[][] result = null;
        if (results.length() > 0) {
            String[] lines = results.split("\n");
            int columnsNumber = lines[0].split("\t").length;
            String parts[];
            result = new String[columnsNumber][lines.length];
            for (int i = 0; i < lines.length; i++) {
                parts = lines[i].split("\t");
                for (int j = 0; j < parts.length; j++) {
                    result[j][i] = parts[j];
                }
            }
        }
        return result;
    }
    
    
    /**
     * Purge the results by removing all the columns that contains a constant value
     * results[n] represents the nth column of the results
     * results[n][m] represents the mth cell of the nth column
     **/
    static public String[][] purgeResults(String[][] results) {
        int columsNumber = results.length;
        int linesNumber = results[0].length;
        ArrayList columnsToRemove = new ArrayList();
        boolean allValuesOfColumnAreEqual;
        for (int i = 0; i < columsNumber; i++) {
            allValuesOfColumnAreEqual = true;
            for (int j = 2; j < linesNumber; j++) { // j starts at 2 because we skip the header (1st line)
                if (!results[i][j].equalsIgnoreCase(results[i][j-1])) {
                    allValuesOfColumnAreEqual = false;
                    break;
                }
           }
           if (allValuesOfColumnAreEqual == true) {
                columnsToRemove.add(i);
            }
        }
        
         String[][] purgedResults = new String[columsNumber - columnsToRemove.size()][linesNumber];
        
         int numberOfRemovedLines = 0;
         for (int i = 0; i < columsNumber; i++) {
            if (!columnsToRemove.contains(i))
                purgedResults[i - numberOfRemovedLines] = results[i];
            else
                numberOfRemovedLines++;
        }
        return purgedResults;
    }
    
    static public JFreeChart generateGraph(String xLabel, ArrayList<String> yLabels,
            String xUnit, String yUnit, ArrayList<Curve> curves) {
        return generateGraph(xLabel, yLabels, xUnit, yUnit, curves, 0.0, 0.0);
    }

    static public JFreeChart generateGraph(String xLabel, ArrayList<String> yLabels,
            String xUnit, String yUnit, ArrayList<Curve> curves,
            double xMin, double xMax) {

        int curvesNumber = curves.size();
        String legendName="";
        if (curvesNumber > 0) {
            XYSeriesCollection dataset = new XYSeriesCollection();
            int linesNumber;
            double x, y;
            for (int i = 0; i < curvesNumber; i++) {
                String yLabel = yLabels.get(i);
                legendName = curves.get(i).getHydrationOperationName();
                legendName += ":" + DataTypes.legendNameOf(yLabel);
                if (!yUnit.equalsIgnoreCase("no unit")) {
                    yLabel += " (" + yUnit + ")";
                }
                XYSeries series = new XYSeries(legendName);
                linesNumber = curves.get(i).getYValues().length;
                String [] xValues = curves.get(i).getXValues();
                String [] yValues = curves.get(i).getYValues();
                for (int j = 0; j < linesNumber; j++) {
                    x = Double.parseDouble(xValues[j]);
                    y = Double.parseDouble(yValues[j]);
                    series.add(x,y);
                }
                dataset.addSeries(series);
            }
            
            if (xUnit.equalsIgnoreCase("no unit"))
                xUnit = "";
            if (yUnit.equalsIgnoreCase("no unit"))
                yUnit = "";
            
            String yLabel;
            if (yLabels.size() == 1) {
                if (yUnit.length() > 0)
                    yLabel = yLabels.get(0) + " (" + yUnit + ")";
                else
                    yLabel = yLabels.get(0);
            } else {
                yLabel = yUnit;
            }
            
            if (xUnit.length() > 0)
                xLabel = xLabel + " (" + xUnit + ")";
            
            // Generate the graph
            JFreeChart chart = ChartFactory.createXYLineChart(null, // Title
                    xLabel, // x-axis Label
                    yLabel, // y-axis Label
                    dataset, // Dataset
                    PlotOrientation.VERTICAL, // Plot Orientation
                    true, // Show Legend
                    true, // Use tooltips
                    false // Configure chart to generate URLs?
                    );
            
            ArrayList<String> styles = getLineStyles();
            ArrayList<Color> colors = getLineColors();
            
            for (int i = 0; i < curvesNumber; i++) {
                setSeriesStyle(chart,i,styles.get(i%(styles.size())));
                setSeriesColor(chart,i,colors.get(i%(colors.size())));
            }

            chart.setBackgroundPaint(Color.white);
            
            chart.getXYPlot().getDomainAxis().setLabelFont(new Font(null,Font.PLAIN,14));
            chart.getXYPlot().getRangeAxis().setLabelFont(new Font(null,Font.PLAIN,14));
            chart.getLegend().setItemFont(new Font(null,Font.PLAIN,14));
            
            /**
             * Get the lowest y value for the given x range
             * Isn't there a function in JFreeChart to do that?
             **/

            double yMin = Integer.MAX_VALUE;
            double yMax = Integer.MIN_VALUE;
            double xValue = 0.0;
            double yValue = 0.0;
            if (xMin > 0.0 || xMax > 0.0) {
                // If we are here, then the user specified an x range
                // to zoom
                for (int j = 0; j < dataset.getSeriesCount(); j++) {
                    for (int i = 0; i < dataset.getItemCount(j); i++) {
                        xValue = dataset.getXValue(j,i);
                        yValue = dataset.getYValue(j,i);
                        if (yValue < yMin)
                            yMin = yValue;
                        if (yValue > yMax)
                            yMax = yValue;
                    }
                }
            } else {
                // if we are here, then we are just trying to find a
                // nice x range and y range to display all the data
                xMin = Integer.MAX_VALUE;
                xMax = Integer.MIN_VALUE;
                for (int j = 0; j < dataset.getSeriesCount(); j++) {
                    for (int i = 0; i < dataset.getItemCount(j); i++) {
                        xValue = dataset.getXValue(j,i);
                        yValue = dataset.getYValue(j,i);
                        if (yValue < yMin)
                            yMin = yValue;
                        if (yValue > yMax)
                            yMax = yValue;
                        if (xValue < xMin)
                            xMin = xValue;
                        if (xValue > xMax)
                            xMax = xValue;
                   }
               }
            }
            
            /**
             * Add 5% margin (except if value == 0, because it would not look nice)
             **/
            if (yMax != 0)
                yMax += Math.abs(yMax - yMin) * 5 / 100;
            if (yMin != 0)
                yMin -= Math.abs(yMax - yMin) * 5 / 100;
            
            if (xMax > xMin)
                chart.getXYPlot().getDomainAxis().setRange(xMin,xMax);
            if (yMax > yMin)
                chart.getXYPlot().getRangeAxis().setRange(yMin,yMax);
            
            return chart;
            
            /*
            try {
                File smallImage = new File(ServerFile.getOperationDir(operationName)+ "graph_small.jpg");
                ChartUtilities.saveChartAsJPEG(smallImage, chart, 512, 384);
                File bigImage = new File(ServerFile.getOperationDir(operationName)+ "graph_big.jpg");
                ChartUtilities.saveChartAsJPEG(bigImage, chart, 1024, 768);
            } catch (IOException e) {
                System.err.println("Problem occurred creating chart.");
            }*/
        }
        return null;
    }

   /**
    * Get styles for the lines that are plotted in generateGraph
    *
    * @return ArrayList of the styles
    */
    private static ArrayList<String> getLineStyles() {
        ArrayList<String> lineStyles = new ArrayList(12);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_LINE);
        lineStyles.add(Constants.STYLE_DASH);
        lineStyles.add(Constants.STYLE_DASH);
        lineStyles.add(Constants.STYLE_DASH);
        lineStyles.add(Constants.STYLE_DASH);
        lineStyles.add(Constants.STYLE_DASH);
        lineStyles.add(Constants.STYLE_DASH);
        return lineStyles;
    }

   /**
    * Get colors for the lines that are plotted in generateGraph
    *
    * @return ArrayList of the colors
    */
    private static ArrayList<Color> getLineColors() {
        ArrayList<Color> lineColors = new ArrayList(12);
        lineColors.add(Color.black);
        lineColors.add(Color.red);
        lineColors.add(Color.blue);
        lineColors.add(Color.green);
        lineColors.add(Color.cyan);
        lineColors.add(Color.magenta);
        lineColors.add(Color.black);
        lineColors.add(Color.red);
        lineColors.add(Color.blue);
        lineColors.add(Color.green);
        lineColors.add(Color.cyan);
        lineColors.add(Color.magenta);
        return lineColors;
    }

   private static BasicStroke toStroke(String style) {
        BasicStroke result = null;

        if (style != null) {
            float lineWidth = 2.0f;
            float dash[] = {5.0f};
            float dot[] = {lineWidth};

            if (style.equalsIgnoreCase(Constants.STYLE_LINE)) {
                result = new BasicStroke(lineWidth);
            } else if (style.equalsIgnoreCase(Constants.STYLE_DASH)) {
                result = new BasicStroke(lineWidth, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10.0f, dash, 0.0f);
            } else if (style.equalsIgnoreCase(Constants.STYLE_DOT)) {
                result = new BasicStroke(lineWidth, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 2.0f, dot, 0.0f);
            }
        }//else: input unavailable

        return result;
    }//toStroke()

    /**
     * Set color of series.
     *
     * @param chart JFreeChart.
     * @param seriesIndex Index of series to set color of (0 = first series)
     * @param style One of STYLE_xxx.
     */
    public static void setSeriesStyle(JFreeChart chart, int seriesIndex, String style) {
        if (chart != null && style != null) {
            BasicStroke stroke = toStroke(style);

            Plot plot = chart.getPlot();
            if (plot instanceof CategoryPlot) {
                CategoryPlot categoryPlot = chart.getCategoryPlot();
                CategoryItemRenderer cir = categoryPlot.getRenderer();
                try {
                    cir.setSeriesStroke(seriesIndex, stroke); //series line style
                } catch (Exception e) {
                    System.err.println("Error setting style '"+style+"' for series '"+seriesIndex+"' of chart '"+chart+"': "+e);
                }
            } else if (plot instanceof XYPlot) {
                XYPlot xyPlot = chart.getXYPlot();
                XYItemRenderer xyir = xyPlot.getRenderer();
                try {
                    xyir.setSeriesStroke(seriesIndex, stroke); //series line style
                } catch (Exception e) {
                    System.err.println("Error setting style '"+style+"' for series '"+seriesIndex+"' of chart '"+chart+"': "+e);
                }
            } else {
                System.out.println("setSeriesColor() unsupported plot: "+plot);
            }
        }//else: input unavailable
    }//setSeriesStyle()

    /**
    * Set color of series.
    *
    * @param chart JFreeChart.
    * @param seriesIndex Index of series to set color of (0 = first series)
    * @param color New color to set.
    */
   public static void setSeriesColor(JFreeChart chart, int seriesIndex, Color color) {
        if (chart != null) {
            Plot plot = chart.getPlot();
            try {
                if (plot instanceof CategoryPlot) {
                    CategoryPlot categoryPlot = chart.getCategoryPlot();
                    CategoryItemRenderer cir = categoryPlot.getRenderer();
                    cir.setSeriesPaint(seriesIndex, color);
                } else if (plot instanceof PiePlot) {
                    PiePlot piePlot = (PiePlot) chart.getPlot();
                    piePlot.setSectionPaint(seriesIndex, color);
                } else if (plot instanceof XYPlot) {
                    XYPlot xyPlot = chart.getXYPlot();
                    XYItemRenderer xyir = xyPlot.getRenderer();
                    xyir.setSeriesPaint(seriesIndex, color);
                } else {
                    System.out.println("setSeriesColor() unsupported plot: "+plot);
                }
            } catch (Exception e) { //e.g. invalid seriesIndex
                System.err.println("Error setting color '"+color+"' for series '"+seriesIndex+"' of chart '"+chart+"': "+e);
            }
        }//else: input unavailable
    }//setSeriesColor()
}
