module sequence_fsm (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       start,
    input  logic       fault,
    input  logic       complete,
    output logic       busy,
    output logic       error_flag,
    output logic [1:0] state_debug
);
    typedef enum logic [1:0] {
        S_IDLE  = 2'b00,
        S_PREP  = 2'b01,
        S_RUN   = 2'b10,
        S_ERROR = 2'b11
    } state_t;

    state_t state, next_state;

    // DELIBERATE DEFECT:
    // fault in S_RUN transitions to S_PREP, making S_ERROR unreachable.
    always @(*) begin
        next_state = state;
        case (state)
            S_IDLE: begin
                if (start) begin
                    next_state = S_PREP;
                end
            end
            S_PREP: begin
                next_state = S_RUN;
            end
            S_RUN: begin
                if (fault) begin
                    next_state = S_PREP;
                end else if (complete) begin
                    next_state = S_IDLE;
                end
            end
            S_ERROR: begin
                if (!fault) begin
                    next_state = S_IDLE;
                end
            end
            default: next_state = S_IDLE;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE;
        end else begin
            state <= next_state;
        end
    end

    assign busy = (state == S_PREP) || (state == S_RUN);
    assign error_flag = (state == S_ERROR);
    assign state_debug = state;
endmodule
