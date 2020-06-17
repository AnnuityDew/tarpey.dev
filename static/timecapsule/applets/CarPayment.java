/*Michael Tarpey
 *Block 1A
 *5-18-09*/
 
 import javax.swing.*;
 import java.awt.event.*;
 import java.awt.*;
 import java.text.DecimalFormat;
  
 public class CarPayment extends JApplet implements ActionListener
 {
 	private JTextField price, downPayment, tradeInAmount, interestRate, loanLength, carName;
 	private JLabel priceL, downPaymentL, tradeInAmountL, interestRateL, loanLengthL, carNameL, resultLabel;
 	private String priceS, downPaymentS, tradeInAmountS, interestRateS, loanLengthS, carNameS;
 	private double p, dP, iR, tIA, monthlyPayment;
 	private int lL;
 	private JButton calculate, clear;
 	
 	DecimalFormat price00 = new DecimalFormat ("0.00");
 	
 	public void init()
 	{
 		Container car = getContentPane();
 		FlowLayout flow = new FlowLayout();
 		car.setLayout(flow);
 		
 		car.setBackground(Color.green);
 		
 		priceL = new JLabel("Price (only use numbers and a decimal point, if needed)");
 		car.add(priceL);
 		price = new JTextField(10);
 		car.add(price);
 		
 		clear = new JButton("Clear All Fields");
 		car.add(clear);
 		clear.addActionListener(this);
 		
 		downPaymentL = new JLabel("Down payment (only use numbers and a decimal point, if needed)");
 		car.add(downPaymentL);
 		downPayment = new JTextField(7);
 		car.add(downPayment);
 		
 		tradeInAmountL = new JLabel("Trade-in value (only use numbers and a decimal point, if needed)");
 		car.add(tradeInAmountL);
 		tradeInAmount = new JTextField(7);
 		car.add(tradeInAmount);
 		
 		interestRateL = new JLabel("Interest rate");
 		car.add(interestRateL);
 		interestRate = new JTextField(4);
 		car.add(interestRate);
 		
 		loanLengthL = new JLabel("Length of the loan (in years)");
 		car.add(loanLengthL);
 		loanLength = new JTextField(4);
 		car.add(loanLength);
 		
 		carNameL = new JLabel("Car Name");
 		car.add(carNameL);
 		carName = new JTextField(15);
 		car.add(carName);
 		
 		calculate = new JButton("Calculate"); 		
 		car.add(calculate);
 		calculate.addActionListener(this);
 		resultLabel = new JLabel("Monthly payment will appear here.");
 		car.add(resultLabel);
 		
 	}
 	
 	public void actionPerformed(ActionEvent event)
 	{
 		Object source = event.getSource();
 		if(source == calculate)
	 	{ 	 		
	 		priceS = price.getText();
	 		downPaymentS = downPayment.getText();
	 		tradeInAmountS = tradeInAmount.getText();
	 		interestRateS = interestRate.getText();
	 		loanLengthS = loanLength.getText();
	 		carNameS = carName.getText();
	 
	 		p = Double.parseDouble(priceS);
	 		dP = Double.parseDouble(downPaymentS);
	 		iR = ((Double.parseDouble(interestRateS)) / 1200);
	 		lL = (Integer.parseInt(loanLengthS)) * 12;
	 		tIA = Double.parseDouble(tradeInAmountS);
	 		
	 		monthlyPayment = (iR + (iR / ((Math.pow((1 + iR), lL)) - 1))) * ((p - dP) - tIA);
			String answer = ("$" + price00.format(monthlyPayment));
			resultLabel.setText(answer);		
			repaint();
	 	}
	 	if(source == clear)
	 	{
	 		price.setText("");
	 		downPayment.setText("");
	 		tradeInAmount.setText("");
	 		interestRate.setText("");
	 		loanLength.setText("");
	 		carName.setText("");
	 		
	 		resultLabel.setText("Monthly payment will appear here.");
	 	}
	}

 }