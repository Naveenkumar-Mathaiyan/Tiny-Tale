# Update your existing deployment

Extract the release ZIP and run APPLY-UPDATE.bat. Select your original Git repository containing app.py and .git. The update reuses static/images and the existing database; it is not a new empty-project installation.

Commit and push the update, then deploy latest commit on both tiny-tale-admin and tiny-tale-store in Render. Keep working Brevo and database environment settings. Both health URLs must show 6.0-store-experience. Press Ctrl+F5 in the browser after deployment.

Owner login: username blank, existing admin password. Store keeper accounts remain restricted to stock and product media. Only Admin/Super admin can edit offer banners and the scrolling strip.

## Custom banner links

Storefront content > Offer banners > Add/Edit > Button destination > Custom URL / store link.
Examples:
- /?product=2#collection — opens the product whose ID is 2.
- #collection — scrolls to products.
- #about — scrolls to About Tiny Tale.
- /policies — opens policies.
- https://your-website.com/offer — opens your external HTTPS page.
The path must exist on the destination site. Product dropdown shortcuts avoid typing product IDs. Select No button for an image-only banner. Optional Open destination in a new tab checkbox.

## Top scrolling strip

Storefront content > Scrolling offer strip. Edit messages and optional destinations, choose speed, enable and Publish strip. Refresh the customer store to see it. Use login as a destination to open email login. This text does not change the actual discount: manage coupons separately. Free delivery still begins at INR 999 subtotal before discounts.

## Customer features to check

Filter by size/price/availability and clear filters; open a product and swipe or use gallery controls; check a delivery PIN; add to bag and view free-delivery progress; browse recently viewed items or clear history; login via real OTP and complete the existing test checkout. Recent history and favourites are stored in that browser, not synced across devices.

## Admin mobile use

Tap Sections to open the grouped menu, then choose a screen. Products & stock uses cards on narrow screens. Existing financial permissions and report exports remain unchanged.
