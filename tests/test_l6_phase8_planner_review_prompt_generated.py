from tiangong_kernel.l6_plugins.final_closure import L6PlannerReviewPrompt

def test_planner_review_prompt_generated():
    prompt = L6PlannerReviewPrompt()
    assert prompt.output_template_ref.startswith('summary:')
    assert prompt.role_count == 18
