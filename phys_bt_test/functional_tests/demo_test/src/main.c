#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

extern void central_main(void);
extern void peripheral_main(void);

int main(void)
{
    printk("Starting Physical Bluetooth Test...\n");

#if defined(CONFIG_BT_CENTRAL)
    printk("Role: CENTRAL\n");
    central_main();
#elif defined(CONFIG_BT_PERIPHERAL)
    printk("Role: PERIPHERAL\n");
    peripheral_main();
#else
    printk("Error: No role defined!\n");
#endif

    return 0;
}
