/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

/**
 *
 * @author bullard
 */
public class Curve {

        /**
         * Holds value of property xValues.
         */
        private String[] xValues;

        /**
         * Getter for property xValues.
         * @return Value of property xValues.
         */
        public String[] getXValues() {
            return this.xValues;
        }

        /**
         * Setter for property xValues.
         * @param xValues New value of property xValues.
         */
        public void setXValues(String[] xValues) {
            this.xValues = xValues;
        }

        /**
         * Holds value of property yValues.
         */
        private String[] yValues;

        /**
         * Getter for property yValues.
         * @return Value of property yValues.
         */
        public String[] getYValues() {
            return this.yValues;
        }

        /**
         * Setter for property yValues.
         * @param yValues New value of property yValues.
         */
        public void setYValues(String[] yValues) {
            this.yValues = yValues;
        }

        /**
         * Holds value of property hydrationOperationName.
         */
        private String hydrationOperationName;

        /**
         * Getter for property hydrationOperationName.
         * @return Value of property hydrationOperationName.
         */
        public String getHydrationOperationName() {
            return this.hydrationOperationName;
        }

        /**
         * Setter for property hydrationOperationName.
         * @param hydrationOperationName New value of property hydrationOperationName.
         */
        public void setHydrationOperationName(String hydrationOperationName) {
            this.hydrationOperationName = hydrationOperationName;
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
         * Constructor for Curve
         * @param name
         */

        public Curve(String[] xValues, String[] yValues, String hydrationOperationName,
                String hydrationProperty) {
            this.xValues = xValues;
            this.yValues = yValues;
            this.hydrationOperationName = hydrationOperationName;
            this.hydrationProperty = hydrationProperty;
        }
    }
