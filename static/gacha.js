async function pull(amount){
	const payload={
        amount:amount
    };
    const response=await fetch('/gacha',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
    });

    console.log(response);

    if (response.ok) {
    	alert(`successfully pulled ${amount} times`);
    }else{
    	alert(`error occured or sth`);
    };
};