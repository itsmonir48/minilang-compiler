# Build the Flex programs into lex/build/.   Usage:  make -C lex   /   make -C lex demo
PROGS := minilang wc numbers urls_emails strip_comments
BUILD := build

all: $(addprefix $(BUILD)/,$(PROGS))

$(BUILD)/%: %.l | $(BUILD)
	flex -o $(BUILD)/$*.yy.c $<
	gcc -O2 -o $@ $(BUILD)/$*.yy.c

$(BUILD):
	mkdir -p $(BUILD)

demo: all
	@echo "== minilang.l on examples/factorial.mini"; $(BUILD)/minilang ../examples/factorial.mini | head -12
	@echo "== wc.l";             $(BUILD)/wc samples/text.txt
	@echo "== numbers.l";        $(BUILD)/numbers samples/text.txt
	@echo "== urls_emails.l";    $(BUILD)/urls_emails samples/text.txt
	@echo "== strip_comments.l"; $(BUILD)/strip_comments samples/comments.c

clean:
	rm -rf $(BUILD)

.PHONY: all demo clean
