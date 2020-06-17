/*Michael Tarpey
 *Block 1A
 *5-18-09*/
 
 import javax.swing.*;
 import java.awt.event.*;
 import java.awt.*;
 import java.text.DecimalFormat;
 import java.util.ArrayList;

  
 public class DoYouKnowMe extends JApplet implements ActionListener
 {
 	private JLabel question, score, choiceA, choiceB, choiceC, choiceD;
 	private double p, dP, iR, tIA, monthlyPayment;
 	private int points = 0;
 	private int questionIndex = 0;
 	private JButton a, b, c, d, restart;
 	private String one, two, three, four, five, six, seven, eight, nine, ten;
 	ArrayList<String> questions = new ArrayList<String>();
 	ArrayList<String> aa = new ArrayList<String>();
 	ArrayList<String> ba = new ArrayList<String>();
 	ArrayList<String> ca = new ArrayList<String>();
 	ArrayList<String> da = new ArrayList<String>();
 	Container quiz = getContentPane();
 	
 	public void init()
 	{
 		FlowLayout flow = new FlowLayout();
 		quiz.setLayout(flow);
 		
 		quiz.setBackground(Color.green);
 		
 		JPanel group = new JPanel();
 		group.setBackground(Color.green);
 		group.setLayout(new GridLayout(9, 2));
 		
		a = new JButton("A");
		quiz.add(a);
		a.addActionListener(this);
		b = new JButton("B");
		quiz.add(b);
		b.addActionListener(this);
		c = new JButton("C");
		quiz.add(c);
		c.addActionListener(this);
		d = new JButton("D");
		quiz.add(d);
		d.addActionListener(this);
		
		answerSetUp();
		
		begin();
 		
 		score = new JLabel("Score: " + points + " out of 10.");
		quiz.add(score);
 		
 		quiz.add(group, BorderLayout.CENTER);
 		 		
 	}
 	
 	public void actionPerformed(ActionEvent event)
 	{
 		Object source = event.getSource();
 		if(source == a)
	 	{ 	 		
	 		answerCheck(1);
	 	}
	 	if(source == b)
	 	{
	 		answerCheck(2);
	 	}
	 	if(source == c)
	 	{
	 		answerCheck(3);
	 	}
	 	if(source == d)
	 	{
	 		answerCheck(4);
	 	}
	 	if(source == restart)
	 	{
	 		questionIndex = 0;
	 		restart();
	 	}
	}
	
	public void answerCheck(int answer)
	{
		int[] answers = {3, 1, 1, 4, 2, 1, 3, 2, 4, 4};
		if(answers[questionIndex] == answer)
			points++;
		questionIndex++;
		
		if(questionIndex == 10)
		{
			choiceA.setText("");
			choiceB.setText("");
			choiceC.setText("");
			choiceD.setText("");
			question.setText("That's it!");
			score.setText("Score: " + points + " out of 10.");
			restart = new JButton("Try again?");
			quiz.add(restart);
			restart.addActionListener(this);
		}
		question.setText(questions.get(questionIndex));
		choiceA.setText(aa.get(questionIndex));
		choiceB.setText(ba.get(questionIndex));
		choiceC.setText(ca.get(questionIndex));
		choiceD.setText(da.get(questionIndex));
		
		score.setText("Score: " + points + " out of 10.");
				
		repaint();		
	}
	
	public void answerSetUp()
	{
		one = "What's my favorite boolean?";	
		two = "What's my favorite food?";
		three = "What is the battle cry?";
		four = "What's my worst subject?";
		five = "What's my favorite color?";
		six = "What's my hometown?";
		seven = "How many detentions have I been to?";
		eight = "Which of the following did my near-death experience involve?";
		nine = "What's my favorite game?";
		ten = "Which of the four spellings of my last name was never used by my ancestors?";
		
		questions.add(one);
		questions.add(two);
		questions.add(three);
		questions.add(four);
		questions.add(five);
		questions.add(six);
		questions.add(seven);
		questions.add(eight);
		questions.add(nine);
		questions.add(ten);
		
		one = "A. True";	
		two = "A. Corned beef and cabbage";
		three = "A. T-WENTT";
		four = "A. Math";
		five = "A. Red";
		six = "A. Daytona Beach";
		seven = "A. None";
		eight = "A. Fireplace";
		nine = "A. MapleStory";
		ten = "A. Tarpey";
		
		aa.add(one);
		aa.add(two);
		aa.add(three);
		aa.add(four);
		aa.add(five);
		aa.add(six);
		aa.add(seven);
		aa.add(eight);
		aa.add(nine);
		aa.add(ten);
		
		one = "B. False";	
		two = "B. Meatball sub";
		three = "B. OOPS";
		four = "B. Science";
		five = "B. Green";
		six = "B. Port Orange";
		seven = "B. More than three";
		eight = "B. Swimming pool";
		nine = "B. Super Mario Bros. 3";
		ten = "B. Tarpe";
		
		ba.add(one);
		ba.add(two);
		ba.add(three);
		ba.add(four);
		ba.add(five);
		ba.add(six);
		ba.add(seven);
		ba.add(eight);
		ba.add(nine);
		ba.add(ten);
		
		one = "C. Both";	
		two = "C. Shrimp";
		three = "C. Good job Joe";
		four = "C. English";
		five = "C. Blue";
		six = "C. St. Augustine";
		seven = "C. One";
		eight = "C. A bowling ball";
		nine = "C. Sky Shark";
		ten = "C. Tarpy";
		
		ca.add(one);
		ca.add(two);
		ca.add(three);
		ca.add(four);
		ca.add(five);
		ca.add(six);
		ca.add(seven);
		ca.add(eight);
		ca.add(nine);
		ca.add(ten);
		
		one = "D. Neither";	
		two = "D. Banana";
		three = "D. OH FALSE";
		four = "D. History";
		five = "D. Black";
		six = "D. Virginia Beach";
		seven = "D. Two";
		eight = "D. My dog";
		nine = "D. Dance Dance Revolution";
		ten = "D. Tarpi";
		
		da.add(one);
		da.add(two);
		da.add(three);
		da.add(four);
		da.add(five);
		da.add(six);
		da.add(seven);
		da.add(eight);
		da.add(nine);
		da.add(ten);
	}
	
	public void begin()
	{
		question = new JLabel(questions.get(0));
 		quiz.add(question);
 				
 		choiceA = new JLabel(aa.get(0));
 		choiceB = new JLabel(ba.get(0));
 		choiceC = new JLabel(ca.get(0));
 		choiceD = new JLabel(da.get(0));
 		quiz.add(choiceA);
 		quiz.add(choiceB);
 		quiz.add(choiceC);
 		quiz.add(choiceD);		
	}
	
	public void restart()
	{
		quiz.remove(restart);
		choiceA.setText(aa.get(0));
		choiceB.setText(ba.get(0));
		choiceC.setText(ca.get(0));
		choiceD.setText(da.get(0));
		question.setText(questions.get(0));
		points = 0;
		score.setText("Score: " + points + " out of 10.");
	}

 }