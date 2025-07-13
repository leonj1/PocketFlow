.PHONY: build run

build:
	./build.sh

run:
	docker run -it -e OPENAI_API_KEY=${OPENAI_API_KEY} -v $(PWD)/output:/app/cookbook/doc-generator/output pocketflow-doc-generator