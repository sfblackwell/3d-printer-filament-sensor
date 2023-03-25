<?php
if ($_SERVER["REQUEST_METHOD"] == "GET") {


	$sqlSecret   = $_GET['sqlsecret'];
	$temperature = $_GET['temperature'];
	$humidity    = $_GET['humidity'];
	$pressure    = $_GET['pressure'];
		
	$onBattery			= $_GET['onBattery'];
	$batteryPercentage	= $_GET['batteryPercentage'];
	$vSystemVolts		= $_GET['vSystemVolts'];
	$fullBattery		= $_GET['fullBattery'];
	$emptyBattery		= $_GET['emptyBattery'];
	$changeBattery		= $_GET['changeBattery'];
		
	echo "<br>temperature: " . $temperature;
	echo "<br>humidity: "    . $humidity;
	echo "<br>pressure: "    . $pressure;
	
	$servername = "localhost";
	$username   = "user";
	$password   = "password";
	$dbname     = "dbname";
	
	$conn = new mysqli($servername, $username, $password, $dbname);

	if ($conn->connect_error) {
		die("Connection failed: " . $conn->connect_error);
		}
	else {
		$sql = "SELECT password FROM credentials where servicename = 'PHPSQLsecret' and username = 'none' and active = 'true' ORDER BY id LIMIT 1";	
		$result = $conn->query($sql);
	
		if ($result->num_rows > 0) {
			while($row = $result->fetch_assoc()) {
				$password = $row["password"];
				}
			}
		
			if ($sqlSecret <> $password) {
				die("Invalid sqlSecret");
			}		
		
		//	secret ok 
		
		$sql = "INSERT INTO filamentSensor (temperature, humidity, pressure, onBattery, batteryPercentage, vSystemVolts, fullBattery, emptyBattery, changeBattery) VALUES ('$temperature', '$humidity', '$pressure', '$onBattery', '$batteryPercentage', '$vSystemVolts', '$fullBattery', '$emptyBattery', '$changeBattery')";	
		if (mysqli_query($conn, $sql)) {
			echo "<br><br>New record created successfully";
		} else {
			echo "<br>Error: " . $sql . "<br>" . mysqli_error($conn);
		}
		mysqli_close($conn);
	}
}
?>
