function checkForMatch(){
	//sends request to check if matched
	fetch("/check_for_match")
		.then(response=>response.json())
		.then(data=>{
			if(data.matched){
				//redirects to matched match
				window.location.href=`/match/${data.match_id}`;
			}else{
				//if unmatched, re-check after 1 second
				setTimeout(checkForMatch,1000);
			}
		});
};

checkForMatch();