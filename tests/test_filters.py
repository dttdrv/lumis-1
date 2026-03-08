from __future__ import annotations

from lumis1.filters import apply_row_filters


def test_apply_row_filters_drops_known_bad_rows_and_keeps_clean_rows() -> None:
    rows = [
        {
            "messages": [
                {"role": "user", "content": "   "},
                {"role": "assistant", "content": "x"},
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "x"},
            ],
            "is_toxic": True,
        },
        {
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "<think>secret</think>"},
            ],
            "thinking": "off",
            "chat_template_kwargs": {"enable_thinking": False},
        },
        {
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Clean answer"},
            ],
            "thinking": "off",
            "chat_template_kwargs": {"enable_thinking": False},
        },
    ]

    kept, report = apply_row_filters(rows)
    assert len(kept) == 1
    assert kept[0]["messages"][1]["content"] == "Clean answer"
    assert report["drop_reasons"]["empty_user_prompt"] == 1
    assert report["drop_reasons"]["toxic_flagged"] == 1
    assert report["drop_reasons"]["cot_marker_detected"] == 1
