package org.koitharu.kotatsu.list.ui.adapter

import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.view.ViewGroup
import androidx.appcompat.R as appcompatR
import androidx.core.graphics.ColorUtils
import androidx.core.view.isVisible
import androidx.core.view.updateLayoutParams
import com.hannesdorfmann.adapterdelegates4.dsl.adapterDelegateViewBinding
import org.koitharu.kotatsu.R
import org.koitharu.kotatsu.core.ui.list.AdapterDelegateClickListenerAdapter
import org.koitharu.kotatsu.core.ui.list.OnListItemClickListener
import org.koitharu.kotatsu.core.util.ext.getThemeColor
import org.koitharu.kotatsu.core.util.ext.getThemeDimensionPixelOffset
import org.koitharu.kotatsu.core.util.ext.setTooltipCompat
import org.koitharu.kotatsu.databinding.ItemMangaGridBinding
import org.koitharu.kotatsu.list.ui.ListModelDiffCallback.Companion.PAYLOAD_PROGRESS_CHANGED
import org.koitharu.kotatsu.list.ui.model.ListModel
import org.koitharu.kotatsu.list.ui.model.MangaGridModel
import org.koitharu.kotatsu.list.ui.model.MangaListModel
import org.koitharu.kotatsu.list.ui.size.ItemSizeResolver

fun mangaGridItemAD(
	sizeResolver: ItemSizeResolver,
	clickListener: OnListItemClickListener<MangaListModel>,
) = adapterDelegateViewBinding<MangaGridModel, ListModel, ItemMangaGridBinding>(
	{ inflater, parent -> ItemMangaGridBinding.inflate(inflater, parent, false) },
) {

	AdapterDelegateClickListenerAdapter(this, clickListener).attach(itemView)

	// Tema (skema warna ekspresif) yang menentukan judul digambar di atas sampul
	// atau di bawahnya. Dulu ini dibaca dari preferensi mentah yang tidak pernah
	// ditulis oleh layar Pengaturan, sehingga pilihan warna ekspresif tidak
	// pernah berpengaruh.
	val isTitleOverCover = binding.textViewTitleOverlay.isVisible

	val titleView = if (isTitleOverCover) {
		binding.textViewTitleOverlay
	} else {
		binding.textViewTitle
	}
	sizeResolver.attachToView(itemView, titleView, binding.progressView)

	binding.viewScrim.isVisible = isTitleOverCover

	val gridSpacing = context.getThemeDimensionPixelOffset(R.attr.mangaGridSpacing)
	itemView.updateLayoutParams<ViewGroup.MarginLayoutParams> {
		setMargins(0, 0, 0, 0)
	}
	itemView.setPadding(gridSpacing, gridSpacing, gridSpacing, if (isTitleOverCover) 0 else gridSpacing)

	if (isTitleOverCover) {
		val darkAccent = ColorUtils.blendARGB(
			context.getThemeColor(appcompatR.attr.colorPrimary),
			Color.BLACK,
			SCRIM_DARKEN,
		)
		binding.viewScrim.background = GradientDrawable(
			GradientDrawable.Orientation.BOTTOM_TOP,
			intArrayOf(
				ColorUtils.setAlphaComponent(darkAccent, 0xF2),
				ColorUtils.setAlphaComponent(darkAccent, 0xC0),
				ColorUtils.setAlphaComponent(darkAccent, 0x00),
			),
		).apply {
			val radius = SCRIM_CORNER_RADIUS_DP * context.resources.displayMetrics.density
			cornerRadii = floatArrayOf(0f, 0f, 0f, 0f, radius, radius, radius, radius)
		}
	}

	bind { payloads ->
		itemView.setTooltipCompat(item.getSummary(context))
		titleView.text = item.title
		binding.progressView.setProgress(item.progress, PAYLOAD_PROGRESS_CHANGED in payloads)
		with(binding.iconsView) {
			clearIcons()
			if (item.isPinned) addIcon(R.drawable.ic_pin_small)
			if (item.isSaved) addIcon(R.drawable.ic_storage)
			isVisible = iconsCount > 0
		}
		binding.imageViewFavourite.isVisible = item.isFavorite
		binding.imageViewCover.setImageAsync(item.coverUrl, item.manga)
		binding.badge.number = item.counter
		binding.badge.isVisible = item.counter > 0
	}
}

private const val SCRIM_DARKEN = 0.78f
private const val SCRIM_CORNER_RADIUS_DP = 12f
