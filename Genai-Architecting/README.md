### Functional Requirements:

1) The hardware would be self-hosted, on-premise
	a) this provides privacy for the end users by running the whole system on company hardware
	b) Costs will be reduced by hosting the 300 users on our own AI Server instead of paying by token

2) Server must be capable of running at least 2 LLMs concurrently 
	a) 1 for language training -- 7b parameters 
	b) 1 for speech training -- parameters depend on model

### Non-functional Requirements:

1) The hardware must cost no more than $10K-$15K
2) Since we are self hosting, our internet has to be an async connection, possibly with a failover

### Assumptions:

1) The models we use would be open source licensed with provision for commercial use
2) Models and site will be updated regularly with newer models to reduce size, latency, and accuracy in response
