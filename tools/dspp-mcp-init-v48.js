// Retry initialization only, while holding the original reservation. tools/call is never replayed here.
async function DPP_MCP_INITIALIZE_331048(initialize,signal){
  for(let attempt=0;attempt<2;attempt++){
    if(signal?.aborted)throw signal.reason??new Error(`Initialization cancelled`);
    try{return await initialize()}catch(error){
      const transient=error?.code===`mcp_http_error`&&error?.retryable===true&&/\bHTTP\s+(?:502|503|504)\b/i.test(String(error?.message??``));
      if(attempt!==0||!transient||signal?.aborted)throw error;
      await new Promise((resolve,reject)=>{
        let timer=null;
        const abort=()=>{clearTimeout(timer);signal?.removeEventListener(`abort`,abort);reject(signal.reason??new Error(`Initialization cancelled`))};
        if(signal?.aborted){abort();return}
        signal?.addEventListener(`abort`,abort,{once:true});
        timer=setTimeout(()=>{signal?.removeEventListener(`abort`,abort);resolve()},350);
      });
    }
  }
}
