import { expect, test } from "@odoo/hoot";
import { mountWithCleanup, makeMockEnv } from "@web/../tests/web_test_helpers";
import { TgrCell } from "@tgr_reports_base/components/cell/cell";

test("TgrCell formats monetary values correctly", async () => {
    const env = await makeMockEnv();
    await mountWithCleanup(TgrCell, {
        env,
        props: {
            cell: {
                name: "1,500.00",
                no_format: 1500,
                figure_type: "monetary",
            }
        },
    });

    expect("td").toHaveClass("numeric");
    expect("td").toHaveClass("text-end");
    expect("td").toHaveTextContent("1,500.00");
    expect("td").not.toHaveClass("text-danger");
});

test("TgrCell shows negative values with danger class", async () => {
    const env = await makeMockEnv();
    await mountWithCleanup(TgrCell, {
        env,
        props: {
            cell: {
                name: "-500.00",
                no_format: -500,
                figure_type: "monetary",
            }
        },
    });

    expect("td").toHaveClass("text-danger");
    expect("td").toHaveTextContent("-500.00");
});
