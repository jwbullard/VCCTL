/*
 * BarChart.java
 *
 * Created on December 17, 2013, 2:02 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.image;

import java.io.*;
import java.util.List;
import java.util.ArrayList;
import java.awt.image.BufferedImage;
import java.awt.Color;
import javax.imageio.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.util.UserDirectory;
import nist.bfrl.vcctl.measurements.*;

import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartUtilities;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.CategoryAxis;
import org.jfree.chart.axis.CategoryLabelPositions;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.plot.CategoryPlot;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.chart.renderer.category.BarRenderer;
import org.jfree.data.category.CategoryDataset;
import org.jfree.data.category.DefaultCategoryDataset;
import org.jfree.ui.ApplicationFrame;
import org.jfree.ui.RefineryUtilities;

/**
 *
 * @author bullard
 */
public class BarChart {
    
    static public BarChart INSTANCE = new BarChart();
    
    static private String current_chart_name = "current-chart.png";
    
    /** Creates a new instance of BarChart */
    protected BarChart() {
    }
    
    private String getCurrentChartPath() {
        String path = Vcctl.getImageDirectory()+current_chart_name;
        
        return path;
    }
    
    public void setBlankChart() {
        String chartPath = getCurrentChartPath();
        // Delete any instance of 'current-chart.png'
        File fpng = new File(chartPath);
        if (fpng.exists()) {
            fpng.delete();
        }
    }
    
    public String createBarChart(String userName, String operationName,
            String dataFileName) throws IOException {
        
        /**
         * Delete chart
         **/
        
        String chartpath = Vcctl.getImageDirectory() + dataFileName;
        File chartFile = new File(chartpath);
        if (chartFile.exists()) {
            chartFile.delete();
        }
 
        
        /**
         * The operation name is the same as the bar chart name
         */
        String inpath = ServerFile.getUserOperationDir(userName, operationName);
        inpath += dataFileName;
        
        /**
         * Create a file name for this chart
         */
        String pngfilename = dataFileName + ".png";
        String pngoutpath = Vcctl.getImageDirectory() + pngfilename;

        boolean success = new File(pngoutpath).delete();
        File fpng = new File(pngoutpath);
        if (!fpng.exists()) {
  
            // Here is where we need to use JFreeChart to make the BarChart
            // Somehow grab the data from the data file (two-column format).

            CategoryDataset dataset = getDataset(inpath);
            JFreeChart jFreeChart = createChart(dataset,"D(um)","f(V)");
            ChartUtilities.saveChartAsPNG(fpng,jFreeChart,200,200);
        }
        System.gc();

        return pngfilename;
    }

    private CategoryDataset getDataset(String inpath) {

        int lineNumber = 1;
        int dataRows = 0;
        String line;
        List<String> poreDiameters = new ArrayList<String>();
        List<String> volumeFractions = new ArrayList<String>();

        String delims = "[\\t ]+";
        String totalPoreVolume = "0";
        try {
            BufferedReader reader = new BufferedReader(new FileReader(inpath));


            // The following reading convention is specific to ascii data
            // files created by the vcctl/cfiles/lib/calcporedist3d function

            // Consult the output format of that function for more information

            while ((line = reader.readLine()) != null) {

                String[] tokens = line.split(delims);

                // If this is the first line, treat specially
                if (lineNumber == 1) {
                    totalPoreVolume = tokens[4];
                } else if (lineNumber > 3) {
                    // This skips the column headings row]
                    String strval = tokens[0];
                    int pdv = Math.round(Float.parseFloat(strval));
                    poreDiameters.add(String.valueOf(pdv));
                    volumeFractions.add(tokens[2]);
                    dataRows++;
                }
                lineNumber++;
            }
            reader.close();
        }
        catch(FileNotFoundException ex) {
            System.out.println("FileNotFoundException : " + ex);
        }
        catch(IOException ioe){
            System.out.println("IOException : " + ioe);
        }

        // All data are now read as strings into poreDiameters and
        // volumeFractions arrays

        // row keys...
        final String series1 = "Pore Volumes";

        // create the dataset...
        final DefaultCategoryDataset dataset = new DefaultCategoryDataset();
        for (int i = 0; i < dataRows; i++) {
            float volumeFractionValue = Float.parseFloat(volumeFractions.get(i));
            dataset.addValue(volumeFractionValue, series1, poreDiameters.get(i));
        }

        return dataset;

    }

    private JFreeChart createChart(CategoryDataset dataset, String xAxisLabel,String yAxisLabel) {
        
        // create the chart...
        final JFreeChart chart = ChartFactory.createBarChart(
            null,                     // chart title
            xAxisLabel,               // domain axis label
            yAxisLabel,               // range axis label
            dataset,                  // data
            PlotOrientation.VERTICAL, // orientation
            false,                     // include legend
            true,                     // tooltips?
            false                     // URLs?
        );

        // NOW DO SOME OPTIONAL CUSTOMISATION OF THE CHART...

        // set the background color for the chart...
        chart.setBackgroundPaint(Color.white);

        // get a reference to the plot for further customisation...
        final CategoryPlot plot = chart.getCategoryPlot();
        plot.setBackgroundPaint(Color.lightGray);
        plot.setDomainGridlinePaint(Color.white);
        plot.setRangeGridlinePaint(Color.white);

        // set the range axis to display integers only...
        // final NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        // rangeAxis.setStandardTickUnits(NumberAxis.createIntegerTickUnits());

        // disable bar outlines...
        final BarRenderer renderer = (BarRenderer) plot.getRenderer();
        renderer.setDrawBarOutline(false);
        

        renderer.setSeriesPaint(0, Color.blue);

        // final CategoryAxis domainAxis = plot.getDomainAxis();
        // domainAxis.setCategoryLabelPositions(
        //    CategoryLabelPositions.createUpRotationLabelPositions(Math.PI / 6.0)
        // );
        // OPTIONAL CUSTOMISATION COMPLETED.
        
        return chart;
        
    }

}