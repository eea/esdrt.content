from operator import methodcaller

SEC_SE_ME = (
    dict(
        title="Draft observations",
        slug="se-my-draft-obs",
        getter=methodcaller("get_draft_observations"),
    ),
    dict(
        title="Draft questions",
        slug="se-my-draft-que",
        getter=methodcaller("get_draft_questions"),
    ),
    dict(
        title="Draft conclusions",
        slug="se-my-draft-con",
        getter=methodcaller("get_draft_conclusions"),
    ),
    dict(
        title="Counterpart questions to comment",
        slug="se-cp-que-com",
        getter=methodcaller("get_counterpart_questions_to_comment"),
    ),
    dict(
        title="Counterpart conclusions to comment",
        slug="se-cp-con-com",
        getter=methodcaller("get_counterpart_conclusion_to_comment"),
    ),
    dict(
        title="MS answers to review",
        slug="se-ms-ans-rev",
        getter=methodcaller("get_ms_answers_to_review"),
    ),
)


SEC_SE_OTHER = (
    dict(
        title="Questions for approval",
        slug="se-obs-approve",
        getter=methodcaller("get_approval_questions"),
    ),
    dict(
        title="Unanswered questions",
        slug="se-unans-que",
        getter=methodcaller("get_unanswered_questions"),
    ),
    dict(
        title="Waiting for comment from counterparts for question",
        slug="se-wait-com-cp-que",
        getter=methodcaller(
            "get_waiting_for_comment_from_counterparts_for_question"
        ),
    ),
    dict(
        title="Waiting for comment from counterparts for conclusion",
        slug="se-wait-com-cp-con",
        getter=methodcaller(
            "get_waiting_for_comment_from_counterparts_for_conclusion"
        ),
    ),
    dict(
        title="Observation for finalisation",
        slug="se-obs-fin",
        getter=methodcaller("get_observation_for_finalisation"),
    ),
)


SEC_LR_ME = (
    dict(
        title="Questions to be sent",
        slug="lr-que-tbs",
        getter=methodcaller("get_questions_to_be_sent"),
    ),
    dict(
        title="Observations to finalise",
        slug="lr-obs-fin",
        getter=methodcaller("get_observations_to_finalise"),
    ),
    dict(
        title="Questions to comment",
        slug="lr-que-com",
        getter=methodcaller("get_questions_to_comment"),
    ),
    dict(
        title="Conclusions to comment",
        slug="lr-con-com",
        getter=methodcaller("get_conclusions_to_comment"),
    ),
)


SEC_LR_TEAM = (
    dict(
        title="Questions with comments from reviewers",
        slug="lr-que-com-rev",
        getter=methodcaller("get_questions_with_comments_from_reviewers"),
    ),
    dict(
        title="Answers from MS",
        slug="lr-ans-ms",
        getter=methodcaller("get_answers_from_ms"),
    ),
)


SEC_LR_MS = (
    dict(
        title="Unanswered questions",
        slug="lr-unans-que",
        getter=methodcaller("get_unanswered_questions_lr_qe"),
    ),
)


SEC_MSC_ME = (
    dict(
        title="Questions from Sector expert to be answered",
        slug="msc-que-se-ans",
        getter=methodcaller("get_questions_to_be_answered"),
    ),
    dict(
        title="Comments received from MS experts",
        slug="msc-com-mse",
        getter=methodcaller("get_questions_with_comments_received_from_mse"),
    ),
    dict(
        title="Finalised with closing remarks",
        slug="msc-final-cr",
        getter=methodcaller("get_observations_with_closing_remarks_msc"),
    ),
)


SEC_MSC_MSE = (
    dict(
        title="Answers requiring comments/discussion from MS experts",
        slug="msc-ans-com-mse",
        getter=methodcaller("get_answers_requiring_comments_from_mse"),
    ),
)


SEC_MSC_SE = (
    dict(
        title="Answers sent to Sector expert",
        slug="msc-ans-se",
        getter=methodcaller("get_answers_sent_to_se_re"),
    ),
)


SEC_MSE_ME = (
    dict(
        title="Comments for answer needed by MS coordinator",
        slug="mse-com-ans-msc",
        getter=methodcaller(
            "get_questions_with_comments_for_answer_needed_by_msc"
        ),
    ),
    dict(
        title="Finalised with closing remarks",
        slug="mse-final-cr",
        getter=methodcaller("get_observations_with_closing_remarks_mse"),
    ),
)


SEC_MSE_MSC = (
    dict(
        title="Observations with my comments still with MSC",
        slug="mse-obs-com-msc",
        getter=methodcaller("get_observations_with_my_comments"),
    ),
)

SEC_MSE_SE = (
    dict(
        title=(
            "Answers that I commented on sent to Sector expert"
        ),
        slug="mse-ans-com-se",
        getter=methodcaller("get_observations_with_my_comments_sent_to_se_re"),
    ),
)


SECTIONS = (
    dict(
        title="Sector expert",
        check=methodcaller("is_sector_expert_or_review_expert"),
        actions=(
            dict(title="My actions", sec=SEC_SE_ME),
            dict(title="Other actions for my observations", sec=SEC_SE_OTHER),
        ),
    ),
    dict(
        title="Quality expert",
        check=methodcaller("is_lead_reviewer_or_quality_expert"),
        actions=(
            dict(title="My actions", sec=SEC_LR_ME),
            dict(title="My teams's actions", sec=SEC_LR_TEAM),
            dict(title="My MS's actions", sec=SEC_LR_MS),
        ),
    ),
    dict(
        title="MS coordinator",
        check=methodcaller("is_member_state_coordinator"),
        actions=(
            dict(title="My actions", sec=SEC_MSC_ME),
            dict(title="MS experts actions", sec=SEC_MSC_MSE),
            dict(title="Sector expert actions", sec=SEC_MSC_SE),
        ),
    ),
    dict(
        title="MS expert",
        check=methodcaller("is_member_state_expert"),
        actions=(
            dict(title="My actions", sec=SEC_MSE_ME),
            dict(title="MSC actions", sec=SEC_MSE_MSC),
            dict(title="Sector expert actions", sec=SEC_MSE_SE),
        ),
    ),
)
